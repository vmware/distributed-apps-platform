#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
import errno
import pickle
import socket
import time

import rpyc

from lydian.apps import config

rpyc.core.protocol.DEFAULT_CONFIG['allow_pickle'] = True


class Manager(object):
    def __init__(self, client):
        self._client = client


class TrafficManger(Manager):

    def delete_traffic_rules(self, endpoint=None):
        self._client.traffic.delete_traffic_rules(endpoint)

    def add_server(self, protocol, port, endpoint, namespace=None):
        self._client.traffic.add_server(protocol, port, endpoint, namespace)

    def start_clients(self):
        self._client.traffic.start_clients()

    def get_traffic_rules(self, endpoint=None):
        return self._client.traffic.get_traffic_rules(endpoint)

    def register_traffic(self, traffic_rules):
        return self._client.traffic.register_traffic(traffic_rules)

    def unregister_traffic(self, traffic_rules):
        self._client.traffic.unregister_traffic(traffic_rules)

    def list_servers(self):
        return self._client.traffic.list_servers()

    def get_server(self, protocol, port):
        return self._client.traffic.get_server(protocol, port)

    def stop_servers(self, namespace=None):
        self._client.traffic.stop_servers(namespace)

    def start_servers(self, namespace=None):
        return self._client.traffic.start_servers(namespace)

    def stop_server(self, protocol, port, namespace=None, endpoint=None):
        self._client.traffic.stop_server(protocol, port, namespace, endpoint)

    def stop_client(self, namespace=None, endpoint=None):
        self._client.traffic.stop_client(namespace, endpoint)

    def stop_clients(self, namespace=None):
        self._client.traffic.stop_clients(namespace)

    def rediscover_namespaces(self):
        self._client.traffic.rediscover_namespaces()


class StatsManager(Manager):

    def get_traffic_stats(self, start_time=None, end_time=None):
        return self._client.stats.get_traffic_stats(
            start_time=start_time, end_time=end_time)

    def get_avg_latency(self, start_time=None, end_time=None):
        return self._client.stats.get_avg_latency(
            start_time=start_time, end_time=end_time)

    def get_failure_count(self, start_time=None, end_time=None,
                          destination=None, port=None, source=None):
        return self._client.stats.get_failure_count(
            start_time=start_time, end_time=end_time,
            destination=destination, port=port, source=source)

    def get_success_count(self, start_time=None, end_time=None,
                          destination=None, port=None, source=None):
        return self._client.stats.get_success_count(
            start_time=start_time, end_time=end_time,
            destination=destination, port=port, source=source)

    def get_failures(self, start_time=None, end_time=None,
                     destination=None, port=None, source=None):
        return self._client.stats.get_failures(
            start_time=start_time, end_time=end_time,
            destination=destination, port=port, source=source)

    def get_successes(self, start_time=None, end_time=None,
                      destination=None, port=None, source=None):
        return self._client.stats.get_successes(
            start_time=start_time, end_time=end_time,
            destination=destination, port=port, source=source)


class NamespaceManager(Manager):

    def list_namespaces(self):
        return self._client.namespace.list_namespaces()

    def get_namespace(self, name):
        return self._client.namespace.get_namespace(name)

    def list_namespaces_ips(self):
        return self._client.namespace.list_namespaces_ips()

    def discover_namespaces(self):
        self._client.namespace.discover_namespaces()


class InterfaceManager(Manager):

    def list_interfaces(self):
        return self._client.interface.list_interfaces()

    def get_interface(self, name, ip=None):
        return self._client.interface.get_interface(name, ip)

    def get_all_ips(self):
        return self._client.interface.get_all_ips()

    def get_ips_by_interface(self, interface):
        return self._client.interface.get_ips_by_interface(interface)

    def get_interface_ips_map(self):
        return pickle.loads(self._client.interface.get_interface_ips_map())


class ResourceMonitorManager(Manager):

    def start(self):
        self._client.monitor.start()

    def stop(self):
        self._client.monitor.stop()

    def is_running(self):
        return self._client.monitor.is_running()


class TCPDumpManager(Manager):

    def start_pcap(self, dst_file, interface='eth0', args=''):
        self._client.tcpdump.start_pcap(dst_file, interface, args)

    def stop_pcap(self, dst_file):
        self._client.tcpdump.stop_pcap(dst_file)

    def is_running(self, dst_file):
        return self._client.tcpdump.is_running(dst_file)


class IperfManager(Manager):

    def start_iperf_server(self, port=None, args=''):
        return self._client.iperf.start_iperf_server(port, args)

    def stop_iperf_server(self, port):
        self._client.iperf.stop_iperf_server(port)

    def start_iperf_client(self, dst_ip, dst_port, duration=10,
                           udp=False, bandwidth=None, args=''):
        return self._client.iperf.start_iperf_client(dst_ip, dst_port,
                                                     duration, udp,
                                                     bandwidth, args)

    def stop_iperf_client(self, job_id):
        self._client.iperf.stop_iperf_client(job_id)

    def get_server_ports(self):
        return self._client.iperf.get_server_ports()

    def get_client_jobs(self):
        return self._client.iperf.get_client_jobs()

    def get_client_job_info(self, job_id):
        return self._client.iperf.get_client_job_info(job_id)

    def is_running(self, port):
        return self._client.iperf.is_running(port)


class ScapyManager(Manager):

    def run(self, code):
        return self._client.scapy.execute(code)

    def get_console(self, params):
        return self._client.scapy.get_console(params)

    def close_session(self, session_id=None):
        self._client.scapy.close_session()


class ConfigManager(Manager):

    def get_param(self, param):
        return self._client.configs.get_param(param)

    def set_param(self, param, val):
        return self._client.configs.set_param(param, val)


class ResultsManager(Manager):

    def traffic(self, reqid, **kwargs):
        return self._client.results.traffic(reqid, **kwargs)

    def get_latency_stat(self, reqid, method, **kwargs):
        return self._client.results.get_latency_stat(reqid=reqid, method=method, **kwargs)

    def get_avg_latency(self, reqid, **kwargs):
        return self._client.results.get_avg_latency(reqid, **kwargs)

    def get_min_latency(self, reqid, **kwargs):
        return self._client.results.get_min_latency(reqid, **kwargs)

    def get_max_latency(self, reqid, **kwargs):
        return self._client.results.get_max_latency(reqid, **kwargs)


class TrafficControllerManager(Manager):

    def register_traffic(self, traffic_rules):
        traffic_rules = pickle.dumps(traffic_rules)
        return self._client.controller.register_traffic(traffic_rules)

    def register_rule(self, trule):
        trule = pickle.dumps(trule)
        return self._client.controller.register_rule(trule)

    def start(self, ruleid):
        self._client.controller.start(ruleid)

    def stop(self, ruleid):
        self._client.controller.stop(ruleid)


class MockTrafficManager(Manager):

    def register_traffic(self, traffic_rules):
        traffic_rules = pickle.dumps(traffic_rules)
        return self._client.controller.register_traffic(traffic_rules)

    def register_rule(self, trule):
        trule = pickle.dumps(trule)
        return self._client.controller.register_rule(trule)

    def start_traffic(self, ruleid):
        self._client.controller.start_traffic(ruleid)

    def stop_traffic(self, ruleid):
        self._client.controller.stop_traffic(ruleid)

    def start(self):
        self._client.controller.start()

    def stop_traffic(self, ruleid):
        self._client.controller.stop()


class LydianClient(object):
    """
    Top level object to access Lydian API
    """

    def __init__(self, host, port=config.get_param('LYDIAN_PORT'),
                 proxy_host=None, request_timeout=180,
                 retry_count=5, sleep_interval=.5):
        """ Initialization of Client object

        :param host: the host IP where lydian service is running
        :type host: str
        :param port: port on which lydian is listening
        :type port: int
        :param proxy_host: ip of the proxy host
        :type proxy_host: str
        :param request_timeout: rpyc request timeout
        :type request_timeout: int
        :param retry_count: no of retries in case of connection failure
        :type retry_count: int
        :type sleep_interval: number of seconds to sleep between retries
        """
        self._host = host
        self._port = port
        self._proxy_host = proxy_host
        self.rpc_client = None
        self._connect(retry_count, sleep_interval, request_timeout)

        # Interface / Namespaces
        self.namespace = NamespaceManager(self.rpc_client.root)
        self.interface = InterfaceManager(self.rpc_client.root)

        # Traffic Apps
        self.traffic = TrafficManger(self.rpc_client.root)
        self.controller = TrafficControllerManager(self.rpc_client.root)

        # Results / Query Apps
        self.stats = StatsManager(self.rpc_client.root)
        self.results = ResultsManager(self.rpc_client.root)

        # Resource Monitor
        self.monitor = ResourceMonitorManager(self.rpc_client.root)
        # Packet Capture
        self.pcap = TCPDumpManager(self.rpc_client.root)
        # IPerf Traffic
        self.iperf = IperfManager(self.rpc_client.root)

        self.scapy = ScapyManager(self.rpc_client.root)
        # Params / Configs
        self.configs = ConfigManager(self.rpc_client.root)

    def _connect(self, retry_count, sleep_interval, request_timeout):

        # Client will wait for request_timeout seconds in case
        # server takes long time to response, default timeout
        # is 30 seconds which is small for few lydian APIs
        conf = {"sync_request_timeout": request_timeout}
        failure_count = 0
        last_exception = None
        while failure_count < retry_count:
            failure_count += 1
            try:
                if self._proxy_host:
                    conn = rpyc.classic.connect(self._proxy_host)
                    self.rpc_client = conn.modules.rpyc.connect(
                        self._host, self._port, config=conf)
                else:
                    self.rpc_client = rpyc.connect(
                        self._host, self._port, config=conf)
                break
            except socket.timeout as e:
                last_exception = e
                time.sleep(sleep_interval)
            except socket.error as e:
                last_exception = e
                if e.errno == errno.ECONNRESET or e.errno == errno.ECONNREFUSED:
                    time.sleep(sleep_interval)
                else:
                    raise
            except Exception:
                raise

        if self.rpc_client is None:
            raise last_exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rpc_client.close()
