#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import collections
import itertools
import logging
import pickle
import queue

import time
import uuid

from lydian.apps import rules
from lydian.apps import config
from lydian.apps.base import BaseApp, exposify
from lydian.apps.internal.setup import SetupInfo
from lydian.apps.monitor import ResourceMonitor
from lydian.apps.recorder import RecordManager
from lydian.controller.client import LydianClient
from lydian.traffic.core import TrafficRule
from lydian.utils.prep import prep_node, cleanup_node
from lydian.utils.parallel import ThreadPool

import lydian.utils.common as common_util
import lydian.utils.install as install

log = logging.getLogger(__name__)

_podium = None


def _get_host_ip(host, func_ip=None):

    if func_ip and callable(func_ip):
        return func_ip(host)

    if getattr(host, 'ip', None):
        func = lambda vm: vm.ip
    else:
        p = get_podium()
        func = p.get_ep_host
    return func(host)


@exposify
class Podium(BaseApp):
    NAME = 'PODIUM'
    HOST_WAIT_TIME = config.get_param('LYDIAN_SERVICE_WAIT_TIME')
    NAMESPACE_INTERFACE_NAME_PREFIXES = config.get_param('NAMESPACE_INTERFACE_NAME_PREFIXES')
    NODE_PREP_MAX_THREAD = config.get_param('NODE_PREP_MAX_THREAD')
    MAX_QUEUE_SIZE = 50000

    def __init__(self, username=None, password=None, db_file=None):
        """
        Podium app for running the show.

        """
        self._primary = True
        self._ep_hosts = {}
        self._ep_username = username or config.get_param('ENDPOINT_USERNAME')
        self._ep_password = password or config.get_param('ENDPOINT_PASSWORD')
        self.rules_app = rules.RulesApp()

        self.traffic_records = None
        self.resource_records = None
        self.monitor = None
        self.db_pool = None
        self.nodes = set()

        # Update config file based on default constants, config file
        # and any previously set configs (in .db file). In that order.
        config.update_config()

        # Generate / update local egg.
        self.update_egg()

    def update_egg(self):
        """
        Updates egg file to be used at endpoints.
        """
        valid_egg_types = ['LOCAL', 'REUSE']
        egg_type = config.get_param('LYDIAN_EGG_TYPE')
        egg_type = egg_type.upper()
        vals = ','.join(valid_egg_types)
        err_msg = "Invalid Egg Type. Valid values are : {%s}" % vals
        assert egg_type in valid_egg_types, err_msg

        if egg_type == 'LOCAL':
            common_util.remove_egg()    # Generate fresh egg.

        # Generate egg from local installtion if egg not already present.
        install.install_egg()

    @property
    def endpoints(self):
        return self._ep_hosts.keys()

    @property
    def ep_hosts(self):
        return self._ep_hosts

    @property
    def rules(self):
        return self.rules_app.rules

    def cleanup(self):
        """
        Deletes local databases.
        """
        self.rules_app.cleanup()
        config.get_configs().cleanup()

    def close(self):
        if self.monitor:
            self.monitor.stop()
        if self.db_pool:
            self.db_pool.stop()

    def start_primary_monitor(self):
        """
        Start Monitoring on Primary node.
        """
        if not self.traffic_records:
            self.traffic_records = queue.Queue(self.MAX_QUEUE_SIZE)
        if not self.resource_records:
            self.resource_records = queue.Queue(self.MAX_QUEUE_SIZE)
        if not self.monitor:
            self.monitor = ResourceMonitor(self.resource_records)
        if not self.db_pool:
            self.db_pool = RecordManager(self.traffic_records,
                                         self.resource_records)
        if self.monitor.stopped():
            self.monitor.start()
        if self.db_pool.stopped():
            self.db_pool.start()

    def is_host_up(self, hostip):
        try:
            with LydianClient(hostip) as client:
                client.monitor.is_running()
            return True
        except Exception:
            return False

    def wait_on_host(self, hostip, wait_time=None):
        wait_time = wait_time or self.HOST_WAIT_TIME
        et = int(time.time() + wait_time)

        while time.time() < et:
            if self.is_host_up(hostip):
                return True

        return False

    def update_endpoints(self, iface_hosts):
        """
        Updates internal Interface Host map with the one provided.

        Parameters
        ----------
        iface_hosts: dict
            Interface- Host that will be added to ep_hosts map.
        """
        self._ep_hosts.update(iface_hosts)

    def remove_endpoints(self, hostip):
        """
        Removes endpoints for the hostip, without disabling the service
        at the host.
        """
        eps = [k for k, v in self._ep_hosts.items() if v == hostip]
        for ep in eps:
            self._ep_hosts.pop(ep)

    def _add_endpoints(self, client, hostip):
        for iface, ips in client.interface.get_interface_ips_map().items():
            if not any([iface.startswith(x) for x in
                        self.NAMESPACE_INTERFACE_NAME_PREFIXES]):
                continue
            for ip in ips:
                self._ep_hosts[ip] = hostip

        # Fetch Namespace Interfaces
        for ip in client.namespace.list_namespaces_ips():
            self._ep_hosts[ip] = hostip

    def add_endpoints(self, hostip, username=None, password=None):
        """
        Add endpoints from the host, reachable by hostip.
        """
        if hostip in self.endpoints:
            log.info("%s is already added.", hostip)
            return

        username = username or self._ep_username
        password = password or self._ep_password

        try:
            with LydianClient(hostip) as client:
                # fetch regular interfaces
                self._add_endpoints(client, hostip)

            self._ep_hosts[hostip] = hostip

        except Exception as err:
            log.error("Error in adding endpoint %s - %r", hostip, err)

    def add_host(self, hostip, username=None, password=None, fetch_iface=True):
        """
        Prepare node and return True on success else False.
        """
        username = username or self._ep_username
        password = password or self._ep_password
        try:
            prep_node(hostip, username, password)
            if not self.wait_on_host(hostip):
                log.error("Could not start service on %s", hostip)
            if fetch_iface:
                self.add_endpoints(hostip, username, password)
            self.nodes.add(hostip)
            return True
        except Exception as err:
            log.error("Error in preparing host %s - %r", hostip, err)
            return False

    def add_hosts(self, hostips, username=None, password=None,
                  fetch_iface=True):
        """
        Prepare Hosts with Lydian service and fetches interface information.
        Returns a dictionary of <key:val> as <hostip:True/False>. True/False
        signify success/failure of operation.
        Parameters
        ------------
        hostips: list
            Collection of (SSH-able) IP addresses.
        username: str
            Username for preparation.
        password: str
            Password for preparation.
        fetch_iface: bool
            Fetch Interface information if set to True.
        """
        if isinstance(hostips, str):
            hostips = hostips.split(',')
        args = [(host, (host, username, password, fetch_iface), {})
                for host in hostips]
        return ThreadPool(self.add_host, args)

    def cleanup_hosts(self, hostips, username=None, password=None,
                      remove_db=True):
        """
        Uninstall Lydian service and optionally remove corresponding dbs on
        remote hosts. Returns a dictionary of <key:val> as <hostip:True/False>.
        True/False signify success/failure of operation.

        Parameters:
        ----------
            hostips: list
                list of (SSH-able) IP addresses
            username: str
            password: str
            remove_db: bool
                remove or retain lydian dbs.
        """
        if isinstance(hostips, str):
            hostips = hostips.split(',')
        args = [(host, (host, username, password), {'remove_db': remove_db})
                for host in hostips]
        results = ThreadPool(cleanup_node, args)

        # Remove all IPs cached in self._ep_hosts for hosts that have
        # successfully cleaned up
        for host_ip, result in results.items():
            if result:
                self.remove_endpoints(host_ip)
                if host_ip in self.nodes:
                    self.nodes.remove(host_ip)
        return results

    def get_ep_host(self, epip):
        return self._ep_hosts.get(epip, None)

    def create_traffic_intent(self, src_ip, dst_ip, dst_port, protocol,
                              reqid=None, connected=True, **kwargs):

        intent = {
            'reqid': reqid or '%s' % uuid.uuid4(),
            'ruleid': '%s' % uuid.uuid4(),
            'src': src_ip,
            'dst': dst_ip,
            'port': dst_port,
            'protocol': protocol,
            'connected': connected
        }
        for k, v in kwargs.items():
            if k in TrafficRule.SCHEMA:
                intent[k] = v
        return intent

    def create_traffic_rule(self, intent):

        trule = TrafficRule()
        for key, value in intent.items():
            setattr(trule, key, value)
        trule.fill()
        return trule

    def run_traffic(self, src_ip, dst_ip, dst_port, protocol,
                    connected=True, duration=-1):
        _intent = self.create_traffic_intent(src_ip, dst_ip, dst_port,
                                             protocol, connected=connected)
        reqid = _intent.get('reqid')
        self.register_traffic([_intent])
        if duration > 0:
            time.sleep(duration)
            self.stop_traffic(reqid)
        return reqid

    def run_mesh_ping(self, hosts, dst_port, protocol, connected=True,
                      duration=-1):
        reqid = '%s' % uuid.uuid4()
        host_pairs = list(itertools.permutations(hosts, 2))
        intents = []
        for src, dst in host_pairs:
            intents.append(self.create_traffic_intent(src, dst, dst_port,
                                                      protocol,
                                                      connected=connected,
                                                      reqid=reqid))
        self.register_traffic(intents)
        if duration > 0:
            time.sleep(duration)
            self.stop_traffic(reqid)
        return reqid

    def register_traffic(self, intent):
        """
        Register Traffic at endpoints. Process rules upfront to register all
        the rules at one endpoint in the single call.

        Parameters
        -----------
        intent : collection (list)
            List of rules to register.
        """
        servers = collections.defaultdict(list)
        clients = collections.defaultdict(list)
        _trules = []
        for rule in intent:
            srchost = self.get_ep_host(rule['src'])
            dsthost = self.get_ep_host(rule['dst'])

            if not srchost:
                log.error("No host found for running traffic from IP : %s",
                          rule['src'])
                continue
            elif not dsthost:
                log.error("No host found for running traffic from IP : %s",
                          rule['dst'])
                continue

            servers[dsthost].append(rule)
            clients[srchost].append(rule)

            trule = self.create_traffic_rule(rule)
            _trules.append(trule)

        # Register at endpoint and create local representation.
        if config.get_param('TRAFFIC_START_SERVERS_FIRST'):
            # Start Servers first and then Clients.
            host_rules_map = [servers, clients]
        else:
            # Start Servers / Clients in single call.
            # May result in some cool off time required before the
            # traffic settles.
            for host, rules in clients.items():
                servers[host].extend(rules)
            host_rules_map = [servers]

        def _register_traffic_rules(host, rules):
            with LydianClient(host) as dclient:
                dclient.controller.register_traffic(rules)

        # Start Server before the client.
        for host_rules in host_rules_map:
            collection = [(host, (host, rules), {})
                          for host, rules in host_rules.items()]
            ThreadPool(_register_traffic_rules, collection)

        self.rules_app.add_rules(_trules)  # Persist rules to local db

    def _traffic_op(self, reqid, op_type):

        def _start_traffic(hostip, rules):
            with LydianClient(hostip) as client:
                client.controller.start(rules)

        def _stop_traffic(hostip, rules):
            with LydianClient(hostip) as client:
                client.controller.stop(rules)

        def _unregister_traffic(hostip, rules):
            with LydianClient(hostip) as client:
                client.controller.unregister_traffic(rules)
                client.results.delete_record(reqid)

        trules = self.get_rules_by_reqid(reqid)

        host_rules = collections.defaultdict(list)
        for trule in trules:
            ruleid = getattr(trule, 'ruleid')
            src_ip = getattr(trule, 'src')
            hostip = self.get_ep_host(src_ip)
            host_rules[hostip].append(ruleid)

        args = [(host, (host, rules), {})
                for host, rules in host_rules.items()]
        if op_type == 'start':
            return ThreadPool(_start_traffic, args)
        elif op_type == 'stop':
            return ThreadPool(_stop_traffic, args)
        elif op_type == 'unregister':
            return ThreadPool(_unregister_traffic, args)

    def start_traffic(self, reqid):
        return self._traffic_op(reqid, op_type='start')

    def stop_traffic(self, reqid, config=False):
        return self._traffic_op(reqid, op_type='stop')

    def unregister_traffic(self, reqid):
        """ Stop traffic, delete rules and result records"""
        results = self._traffic_op(reqid, op_type='unregister')
        self.rules_app.delete(reqid=reqid)
        return results

    def get_rules_by_reqid(self, reqid):
        trules = [trule for rule_id, trule in self.rules.items()
                  if getattr(trule, 'reqid') == reqid]
        return trules

    def get_host_result(self, host_ip, reqid, duration=None, **kwargs):
        if duration is not None:
            # Creating a tuple of range for timestamp field
            latency = config.get_param('TRAFFIC_STATS_QUERY_LATENCY')
            current_time = int(time.time()) - latency
            kwargs['timestamp'] = (str(current_time - duration), str(current_time))

        results = []

        with LydianClient(host_ip) as client:
            results = pickle.loads(client.results.traffic(reqid, **kwargs))

        return results

    def _get_results(self, hostips, reqid, duration=None, **kwargs):
        results = []
        workers = self.NODE_PREP_MAX_THREAD

        args = [(host, (host, reqid, duration), kwargs) for host in hostips]
        _results = ThreadPool(self.get_host_result, args, workers=workers)
        for _, val in _results.items():
            results.extend(val)

        return results

    def get_results(self, reqid, duration=None, **kwargs):
        trules = self.get_rules_by_reqid(reqid)
        hostips = set([self.get_ep_host(rule.src)
                      for rule in trules if rule.src])
        results = self._get_results(hostips, reqid, duration=duration,
                                    **kwargs)
        return results

    def get_traffic_stats(self, reqid, duration=None, **kwargs):
        stats = {'success': 0,
                 'failure': 0}

        _ = kwargs.pop('result', None)
        pass_records = self.get_results(reqid, duration=duration, result='1',
                                        **kwargs)
        fail_records = self.get_results(reqid, duration=duration, result='0',
                                        **kwargs)

        for host_pass_record in pass_records:
            stats['success'] += len(host_pass_record)

        for host_fail_record in fail_records:
            stats['failure'] += len(host_fail_record)

        return stats

    def get_traffic_pass_percent(self, reqid, duration=None, **kwargs):
        stats = self.get_traffic_stats(reqid, duration=duration, **kwargs)
        total = stats['success'] + stats['failure']
        return round(stats['success'] * 100 / total, 2) if total else 0

    def get_traffic_fail_percent(self, reqid, duration=None, **kwargs):
        stats = self.get_traffic_stats(reqid, duration=duration, **kwargs)
        total = stats['success'] + stats['failure']
        return round(stats['failure'] * 100 / total, 2) if total else 100

    def get_param(self, host_ip, param):
        host_ip = self.get_ep_host(host_ip)
        with LydianClient(host_ip) as client:
            return client.configs.get_param(param)

    def set_param(self, host_ip, param, val):
        host_ip = self.get_ep_host(host_ip)
        with LydianClient(host_ip) as client:
            client.configs.set_param(param, val)

    def get_host_latency(self, host_ip, reqid, method, duration=None,
                         **kwargs):
        result = 0
        with LydianClient(host_ip) as client:
            current_time = time.time()
            if duration is not None:
                # Creating a tuple of range for timestamp field
                kwargs['timestamp'] = (str(current_time - duration), str(current_time))
            result = client.results.get_latency_stat(reqid=reqid,
                                                     method=method,
                                                     **kwargs)
        return result

    def _get_latencies(self, trules, reqid, method, duration=None, **kwargs):

        hosts = set()
        for trule in trules:
            src_ip = getattr(trule, 'src')
            hosts.add(self.get_ep_host(src_ip))
        args = [(host, (host, reqid, method, duration), kwargs)
                for host in hosts]

        results = ThreadPool(self.get_host_latency, args)
        latencies = [latency for latency in results.values()]
        return latencies

    def get_latency(self, reqid, method, duration=None, **kwargs):
        trules = self.get_rules_by_reqid(reqid)
        latencies = self._get_latencies(trules, reqid, method,
                                        duration=duration, **kwargs)
        result = 0
        latencies = [latency for latency in latencies if latency is not None]
        if latencies:
            return result

        if method == 'avg':
            result = round(sum(latencies) / len(latencies), 2)
        elif method == 'min':
            result = round(min(latencies), 2)
        elif method == 'max':
            result = round(max(latencies), 2)
        else:
            log.error('Invalid method: %s for get latency', method)

        return result

    def get_avg_latency(self, reqid, duration=None, **kwargs):
        return self.get_latency(reqid, method='avg', duration=duration,
                                **kwargs)

    def get_min_latency(self, reqid, duration=None, **kwargs):
        return self.get_latency(reqid, method='min', duration=duration,
                                **kwargs)

    def get_max_latency(self, reqid, duration=None, **kwargs):
        return self.get_latency(reqid, method='max', duration=duration,
                                **kwargs)

    def start_api_server(self):
        self.setup = SetupInfo()
        self.setup.add_primary_node()
        for hostip in self.nodes:
            self.setup.save_endpoint(hostip)

    def _discover_interfaces(self, hostip):
        """ Helper function to discover interfaces """
        with LydianClient(hostip) as client:
            try:
                client.controller.discover_interfaces()
                self._add_endpoints(client, hostip)
                return True
            except Exception as _:
                return False

    def discover_interfaces(self, hostips):
        """
        Discovers interfaces at runtime on the endpoints.

        Parameters
        ------------
        hostips: list
            List of hostips.
        """
        args = [(h, (h,), {}) for h in hostips]
        return ThreadPool(self._discover_interfaces, args)


def get_podium():
    global _podium
    if not _podium:
        _podium = Podium()

    return _podium


def run_iperf(src, dst, duration=10, udp=False, bandwidth=None,
              client_args='', server_args='', func_ip=None, iperf_bin='iperf3',
              dst_port=None):
    """
    Run iperf between <src> and <dst> over TCP/UDP for <duration> seconds

    Returns iperf client output

    NOTE: By default the transfer rate is unlimited which consumes high CPU

    Parameters
    ----------
    src: host
        iperf client
    dst: host
        iperf server
    duration: int
        How long iperf should run
    udp: bool
        Whether to run in UDP mode or TCP (default: TCP)
    bandwidth: int
        Limit traffic to this many Mbits/second
    client_args: str
        Additional cli options supported by iperf client
    server_args: str
        Additional cli options supported by iperf server
    func_ip: func
        function to resolve endpoint mgmt IP
    iperf_bin: str
        iperf binary path
    dst_port: int
        iperf server port
    """

    src_host = _get_host_ip(src, func_ip)
    dst_host = _get_host_ip(dst, func_ip)
    with LydianClient(dst_host) as server:
        with LydianClient(src_host) as client:
            port, job_id = None, None
            try:
                port = server.iperf.start_iperf_server(port=dst_port,
                                                       args=server_args,
                                                       iperf_bin=iperf_bin)
                log.info('iperf server: %s is running on port %s', dst, port)
                job_id = client.iperf.start_iperf_client(dst, port,
                                                         duration=duration,
                                                         udp=udp,
                                                         bandwidth=bandwidth,
                                                         args=client_args,
                                                         iperf_bin=iperf_bin)
                job_info = client.iperf.get_client_job_info(job_id)
                log.info('cmd: %s on iperf client running with job id: %d',
                         job_info['cmd'], job_id)
                time.sleep(duration)
                while job_info['state'] == 'running':
                    time.sleep(1)
                    job_info = client.iperf.get_client_job_info(job_id)
                    log.info('iperf client job: %d info %s', job_id, job_info)
                return job_info['result']
            finally:
                if port:
                    server.iperf.stop_iperf_server(port)
                    if job_id:
                        client.iperf.stop_iperf_client(job_id)


# Keeping run_iperf3 for backward compatibility
run_iperf3 = run_iperf


def start_pcap(host, pcap_file_name, interface, pcap_args='',
               func_ip=None, tool_path=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.pcap.start_pcap(pcap_file_name, interface, pcap_args, tool_path)


def stop_pcap(host, pcap_file_name, func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.pcap.stop_pcap(pcap_file_name)


def start_resource_monitoring(host, func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.monitor.start()


def stop_resource_monitoring(host, func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.monitor.stop()


def stop_service(hosts, remove_db=True):
    """
    Stops service on hosts.

    Parameters
    ------------
    hosts: collection
        List of hosts
    """
    username = config.get_param('ENDPOINT_USERNAME')
    password = config.get_param('ENDPOINT_PASSWORD')
    args = [(host, (host, username, password, remove_db), {})
            for host in hosts]

    ThreadPool(cleanup_node, args)
