#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging

from axon.client.traffic_controller import TrafficController
from axon.client.axon_client import AxonClient
from axon.client.utils import ParallelWork

log = logging.getLogger(__name__)


def register_traffic(server, rule, proxy_host):
    try:
        with AxonClient(server, proxy_host=proxy_host) as client:
            client.traffic.register_traffic([rule.as_dict()])
    except Exception:
        log.exception("Traffic push on endpoint %s failed" % server)
        return False
    return True


def unregister_traffic(server, rule, proxy_host):
    try:
        with AxonClient(server, proxy_host=proxy_host) as client:
            client.traffic.unregister_traffic([rule.as_dict()])
    except Exception:
        log.exception("Traffic push on endpoint %s failed" % server)
        return False
    return True


def start_servers(server, proxy_host):
    try:
        with AxonClient(server, proxy_host=proxy_host) as client:
            client.traffic.start_servers()
    except Exception:
        log.exception("Starting servers on endpoint %s failed" % server)
        return False
    return True


def start_clients(server, proxy_host):
    try:
        with AxonClient(server, proxy_host=proxy_host) as client:
            client.traffic.start_clients()
    except Exception:
        log.exception("Starting clients on endpoint %s failed" % server)
        return False
    return True


def stop_servers(server, proxy_host):
    try:
        with AxonClient(server, proxy_host=proxy_host) as client:
            client.traffic.stop_servers()
    except Exception:
        log.exception("Stopping servers on endpoint %s failed" % server)
        return False
    return True


def stop_clients(server, proxy_host):
    try:
        with AxonClient(server, proxy_host=proxy_host) as client:
            client.traffic.stop_clients()
    except Exception:
        log.exception("Stopping clients on endpoint %s failed" % server)
        return False
    return True


class TrafficRecord(object):
    def __init__(self, endpoint, servers=None, clients=None):
        self._endpoint = endpoint
        self._servers = servers if servers else []
        self._clients = clients if clients else []

    def add_server(self, protocol, port):
        if (protocol, port) not in self._servers:
            self._servers.append((protocol, port))

    def add_client(self, protocol, port, destination, connected, action):
        if (protocol, port, destination) not in self._clients:
            self._clients.append((
                protocol, port, destination, connected, action))

    def as_dict(self):
        return dict(list(zip(['endpoint', 'servers', 'clients'],
                        [self._endpoint, self._servers, self._clients])))


class BasicTrafficController(TrafficController):

    def __init__(self, gateway_host=None):
        super(BasicTrafficController, self).__init__()
        self._gw_host = gateway_host
        self._servers = dict()
        self.log = logging.getLogger(__name__)

    def __create_rules(self, traffic_config):
        for trule in traffic_config:
            src = str(trule.src_eps.ip_list[0])
            dst = str(trule.dst_eps.ip_list[0])
            if not self._servers.get(src):
                self._servers[str(src)] = TrafficRecord(src)
            if not self._servers.get(str(dst)):
                self._servers[dst] = TrafficRecord(dst)
            self._servers[dst].add_server(trule.protocol, trule.port.port)
            self._servers[src].add_client(
                trule.protocol, trule.port.port,
                dst, trule.connected, trule.action)

    def __execute_work(self, work_list):
        resp = ParallelWork.Do(
            work_list, count=min(200, len(work_list)))
        if not all(resp):
            return False
        return True

    def register_traffic(self, traffic_config):
        self.__create_rules(traffic_config)
        work = []
        for server, rule, gw_host in [(server, rule, self._gw_host) for
                                      server, rule in list(self._servers.items())]:
            work.append([register_traffic, [server, rule, gw_host], {}])
        if not self.__execute_work(work):
            self.log.error("Traffic Push does not succeed on all endpoints")
        self.log.info("Traffic push completed")

    def unregister_traffic(self, traffic_config):
        self.__create_rules(traffic_config)
        work = []
        for server, rule, gw_host in [(server, rule, self._gw_host) for
                                      server, rule in list(self._servers.items())]:
            work.append([unregister_traffic, [server, rule, gw_host], {}])
        if not self.__execute_work(work):
            self.log.error("Traffic Push does not succeed on all endpoints")
        self.log.info("Traffic push completed")

    def __stop_clients(self, servers):
        servers = servers if servers else list(self._servers.keys())
        if not servers:
            return
        work = []
        for server, gw_host in [(server, self._gw_host) for server in servers]:
            work.append([stop_clients, [server, gw_host], {}])
        if not self.__execute_work(work):
            self.log.error("Stop clients does not succeed on all endpoints")
        self.log.info("Stop Clients completed")

    def __stop_servers(self, servers):
        servers = servers if servers else list(self._servers.keys())
        if not servers:
            return
        work = []
        for server, gw_host in [(server, self._gw_host) for server in servers]:
            work.append([stop_servers, [server, gw_host], {}])
        if not self.__execute_work(work):
            self.log.error("Stop servers does not succeed on all endpoints")
        self.log.info("Stop servers completed")

    def __start_servers(self, servers):
        servers = servers if servers else list(self._servers.keys())
        if not servers:
            return
        work = []
        for server, gw_host in [(server, self._gw_host) for server in servers]:
            work.append([start_servers, [server, gw_host], {}])
        if not self.__execute_work(work):
            self.log.error("Start servers does not succeed on all endpoints")
        self.log.info("Start servers completed")

    def __start_clients(self, servers):
        servers = servers if servers else list(self._servers.keys())
        if not servers:
            return
        work = []
        for server, gw_host in [(server, self._gw_host) for server in servers]:
            work.append([start_clients, [server, gw_host], {}])
        if not self.__execute_work(work):
            self.log.error("Start clients does not succeed on all endpoints")
        self.log.info("Start clients completed")

    def stop_traffic(self, servers=None):
        self.__stop_clients(servers)
        self.__stop_servers(servers)

    def start_traffic(self, servers=None):
        self.__start_servers(servers)
        self.__start_clients(servers)

    def restart_traffic(self, servers=None):
        self.stop_traffic(servers)
        self.start_traffic(servers)
