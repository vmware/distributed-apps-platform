#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import collections
import itertools
import logging
import pickle
from multiprocessing.pool import ThreadPool
from queue import Queue
import threading
import time
import uuid

from lydian.apps import rules
from lydian.apps import config
from lydian.apps.base import BaseApp, exposify
from lydian.controller.client import LydianClient
from lydian.traffic.core import TrafficRule
from lydian.utils.prep import prep_node

log = logging.getLogger(__name__)

_podium = None


def _get_host_ip(host, func_ip=None):
    func = lambda vm: vm.ip
    func_ip = func if func_ip is None else func_ip
    return func_ip(host)


@exposify
class Podium(BaseApp):
    NAME = 'PODIUM'

    TENNAT_VM_USERNAME = 'root'
    TENNAT_VM_PASSWORD = '!cisco'

    HOST_WAIT_TIME = 4
    NAMESPACE_INTERFACE_NAME_PREFIXES = config.get_param('NAMESPACE_INTERFACE_NAME_PREFIXES')
    NODE_PREP_MAX_THREAD = config.get_param('NODE_PREP_MAX_THREAD')

    def __init__(self, username=None, password=None, db_file=None):
        """
        Podium app for running the show.

        """
        self._primary = True
        self._ep_hosts = {}
        self._ep_username = username or self.TENNAT_VM_USERNAME
        self._ep_password = password or self.TENNAT_VM_PASSWORD
        self.rules_app = rules.RulesApp()

        # Update config file based on default constants, config file
        # and any previously set configs (in .db file). In that order.
        config.update_config()

    @property
    def endpoints(self):
        return self._ep_hosts.keys()

    @property
    def rules(self):
        return self.rules_app.rules

    def wait_on_host(self, hostip, wait_time=None):
        wait_time = wait_time or self.HOST_WAIT_TIME
        et = int(time.time() + wait_time)

        while time.time() < et:
            if self.is_host_up(hostip):
                return True

        return False

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
                for iface, ips in client.interface.get_interface_ips_map().items():
                    if not any([iface.startswith(x) for x in
                                self.NAMESPACE_INTERFACE_NAME_PREFIXES]):
                        continue
                    for ip in ips:
                        self._ep_hosts[ip] = hostip

                # Fetch Namespace Interfaces
                for ip in client.namespace.list_namespaces_ips():
                    self._ep_hosts[ip] = hostip

            self._ep_hosts[hostip] = hostip

        except Exception as err:
            log.error("Error in adding endpoint %s - %r", hostip, err)

    def _add_hosts(self, params):
        host_ip, username, password = params[0], params[1], params[2]
        self.add_host(host_ip, username=username, password=password)

    def add_hosts(self, hostips, username=None, password=None):
        """ Add remote hosts for installing and starting lydian service.
        Args:
            hostips(str or list):
                a single hostname/IP or comma separated hostnames/IPs or list of hostnames/IPs
            username: username
            password: password
        """
        if isinstance(hostips, str):
            hostips = hostips.split(',')

        pool = ThreadPool(self.NODE_PREP_MAX_THREAD)
        params = [(host, username, password) for host in hostips]
        pool.map(self._add_hosts, params)
        pool.close()
        pool.join()


    def add_host(self, hostip, username=None, password=None):
        username = username or self._ep_username
        password = password or self._ep_password
        try:
            prep_node(hostip, username, password)
            if not self.wait_on_host(hostip):
                log.error("Could not start service on %s", hostip)
            self.add_endpoints(hostip, username, password)
        except Exception as err:
            log.error("Error in preparing host %s - %r", hostip, err)

    def is_host_up(self, hostip):
        try:
            with LydianClient(hostip) as client:
                client.monitor.is_running()
            return True
        except Exception:
            return False

    def get_ep_host(self, epip):
        return self._ep_hosts.get(epip, None)

    def create_traffic_intent(self, src_ip, dst_ip, dst_port, protocol, reqid=None,
                            connected=True, **kwargs):

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

    def run_traffic(self, src_ip, dst_ip, dst_port, protocol, duration=-1):
        _intent = self.create_traffic_intent(src_ip, dst_ip, dst_port, protocol)
        reqid = _intent.get('reqid')
        self.register_traffic([_intent])
        if duration > 0:
            time.sleep(duration)
            self.stop_traffic(reqid)
        return reqid

    def run_mesh_ping(self, hosts, dst_port, protocol, duration=-1):
        reqid = '%s' % uuid.uuid4()
        host_pairs = list(itertools.permutations(hosts, 2))
        intents = []
        for src, dst in host_pairs:
            intents.append(self.create_traffic_intent(src, dst, dst_port, protocol, reqid=reqid))
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

        for host_rules in host_rules_map:
            for host, rules in host_rules.items():
                # Start Server before the client.
                with LydianClient(host) as dclient:
                    dclient.controller.register_traffic(rules)

        # Persist rules to local db
        self.rules_app.add_rules(_trules)

    def _traffic_op(self, reqid, op_type):
        trules = self.get_rules_by_reqid(reqid)
        for trule in trules:
            ruleid = getattr(trule, 'ruleid')
            src_ip = getattr(trule, 'src')
            host_ip = self.get_ep_host(src_ip)
            with LydianClient(host_ip) as client:
                if op_type == 'start':
                    client.controller.start(ruleid)
                elif op_type == 'stop':
                    client.controller.stop(ruleid)

    def start_traffic(self, reqid):
        self._traffic_op(reqid, op_type='start')

    def stop_traffic(self, reqid):
        self._traffic_op(reqid, op_type='stop')

    def get_rules_by_reqid(self, reqid):
        trules = [trule for rule_id, trule in self.rules.items() if getattr(trule, 'reqid') == reqid]
        return trules

    def get_host_result(self, src_ip, reqid, results_q=None, duration=None, **kwargs):
        host_ip = self.get_ep_host(src_ip)
        current_time = int(time.time())
        if duration is not None:
            # Creating a tuple of range for timestamp field
            kwargs['timestamp'] = (str(current_time - duration), str(current_time))

        results = []

        with LydianClient(host_ip) as client:
            results = client.results.traffic(reqid, **kwargs)
            results = pickle.loads(results)

        if results_q:
            results_q.put(results)

        return results

    def _get_results(self, trules, duration=None, **kwargs):
        threads = []
        results_q = Queue()
        for trule in trules:
            src_ip = getattr(trule, 'src')
            req_id = getattr(trule, 'reqid')
            if not src_ip or not req_id:
                log.error("Unable to get src or reqid for rule:%r", trule)
                continue
            thread = threading.Thread(target=self.get_host_result,
                                      args=(src_ip, req_id, results_q, duration),
                                      kwargs=kwargs)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        results = [results_q.get() for _ in range(results_q.qsize())]

        return results

    def get_results(self, reqid, duration=None, **kwargs):
        trules = self.get_rules_by_reqid(reqid)
        results = self._get_results(trules, duration=duration, **kwargs)
        return results

    def get_traffic_stats(self, reqid, duration=None):
        stats = {'success': 0,
                 'failure': 0}

        pass_records = self.get_results(reqid, duration=duration, result='1')
        fail_records = self.get_results(reqid, duration=duration, result='0')

        for host_pass_record in pass_records:
            stats['success'] += len(host_pass_record)

        for host_fail_record in fail_records:
            stats['failure'] += len(host_fail_record)

        return stats

    def get_traffic_pass_percent(self, reqid, duration=None):
        stats = self.get_traffic_stats(reqid, duration=duration)
        total = stats['success'] + stats['failure']
        return round(stats['success'] * 100 / total, 2) if total else 0

    def get_traffic_fail_percent(self, reqid, duration=None):
        stats = self.get_traffic_stats(reqid, duration=duration)
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

    def get_host_latency(self, src_ip, reqid, method, results_q=None, duration=None, **kwargs):
        host_ip = self.get_ep_host(src_ip)

        with LydianClient(host_ip) as client:
            current_time = time.time()
            if duration is not None:
                # Creating a tuple of range for timestamp field
                kwargs['timestamp'] = (str(current_time - duration), str(current_time))
            if results_q:
                results_q.put(client.results.get_latency_stat(reqid=reqid, method=method, **kwargs))
            else:
                return client.results.get_latency_stat(reqid=reqid, method=method, **kwargs)

    def _get_latencies(self, trules, method, duration=None, **kwargs):
        threads = []
        latencies_q = Queue()
        for trule in trules:
            src_ip = getattr(trule, 'src')
            req_id = getattr(trule, 'reqid')
            if not src_ip or not req_id:
                log.error("Unable to get src or reqid for rule:%r", trule)
                continue
            thread = threading.Thread(target=self.get_host_latency,
                                      args=(src_ip, req_id, method, latencies_q, duration),
                                      kwargs=kwargs)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        latencies_q = [latencies_q.get() for _ in range(latencies_q.qsize())]

        return latencies_q

    def get_latency(self, reqid, method, duration=None, **kwargs):
        trules = self.get_rules_by_reqid(reqid)
        latencies = self._get_latencies(trules, method, duration=duration, **kwargs)
        if method == 'avg':
            return round(sum(latencies) / len(latencies), 2)
        elif method == 'min':
            return round(min(latencies), 2)
        elif method == 'max':
            return round(max(latencies), 2)

    def get_avg_latency(self, reqid, duration=None, **kwargs):
        return self.get_latency(reqid, method='avg', duration=duration, **kwargs)

    def get_min_latency(self, reqid, duration=None, **kwargs):
        return self.get_latency(reqid, method='min', duration=duration, **kwargs)

    def get_max_latency(self, reqid, duration=None, **kwargs):
        return self.get_latency(reqid, method='max', duration=duration, **kwargs)


def get_podium():
    global _podium
    if not _podium:
        _podium = Podium()

    return _podium


def run_iperf3(src, dst, duration=10, udp=False, bandwidth=None,
               client_args='', server_args='', func_ip=None):
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
    """
    _podium = get_podium()
    src_host = _podium.get_ep_host(src)
    dst_host = _podium.get_ep_host(dst)
    with LydianClient(dst_host) as server:
        with LydianClient(src_host) as client:
            try:
                port = server.iperf.start_iperf_server(args=server_args)
                log.info('iperf server: %s is running on port %s', dst_host, port)
                job_id = client.iperf.start_iperf_client(dst_host, port, duration, udp, bandwidth,
                                                         args=client_args)
                job_info = client.iperf.get_client_job_info(job_id)
                log.info('cmd: %s on iperf client running with job id: %d', job_info['cmd'],
                         job_id)
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


def start_pcap(host, pcap_file_name, interface, pcap_args='', func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.pcap.start_pcap(pcap_file_name, interface, pcap_args)


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
