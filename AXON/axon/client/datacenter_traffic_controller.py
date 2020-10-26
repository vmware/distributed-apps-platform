#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from collections import defaultdict
import os
import logging
import pickle
from multiprocessing.pool import ThreadPool

from axon.client.traffic_controller import TrafficController, TrafficRecord
from axon.client.axon_client import AxonClient

WORKLOAD_VIF_MAP_FILE_PATH = "/var/lib/axon/workloadvifs/"
WORKLOAD_VIF_MAP_FILE = "workload_vif_map.pkl"
THREADPOOL_SIZE = 50
log = logging.getLogger(__name__)


def register_traffic(register_param):
    workload_server = register_param[0]
    rule_list = register_param[1]
    proxy_host = register_param[2]
    server_port = register_param[3]
    with AxonClient(workload_server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                     sleep_interval=1) as client:
        client.traffic.register_traffic(rule_list)


def start_servers(start_param):
    server = start_param[0]
    proxy_host = start_param[1]
    server_port = start_param[2]
    with AxonClient(server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                    sleep_interval=1) as client:
        client.traffic.start_servers()


def start_clients(start_param):
    server = start_param[0]
    proxy_host = start_param[1]
    server_port = start_param[2]
    with AxonClient(server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                    sleep_interval=1) as client:
        client.traffic.start_clients()


def stop_servers(stop_param):
    server = stop_param[0]
    proxy_host = stop_param[1]
    server_port = stop_param[2]
    with AxonClient(server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                    sleep_interval=1) as client:
        client.traffic.stop_servers()


def stop_clients(stop_param):
    server = stop_param[0]
    proxy_host = stop_param[1]
    server_port = stop_param[2]
    with AxonClient(server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                    sleep_interval=1) as client:
        client.traffic.stop_clients()


def clear_traffic_rules(delete_param):
    server = delete_param[0]
    proxy_host = delete_param[1]
    server_port = delete_param[2]
    with AxonClient(server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                    sleep_interval=1) as client:
        client.traffic.delete_traffic_rules()


def rediscover_namespaces(discover_param):
    server = discover_param[0]
    proxy_host = discover_param[1]
    server_port = discover_param[2]
    with AxonClient(server, proxy_host=proxy_host, axon_port=server_port, retry_count=30,
                    sleep_interval=1) as client:
        client.traffic.rediscover_namespaces()


class WorkloadVifsMap(object):
    def __init__(self):
        self.vif_map_load = False

    def build_workloads_vifs_map(self, workload_ips=[]):
        """
        This function build workloads_vifs_map based on workload_ips and
        dumps this
        :param workload_ips:
        :return: workload_vif_map
        """
        if not workload_ips:
            return "No Workload IPs passed to build workloads vifs map"
        map_dict = {}
        for wip in workload_ips:
            with AxonClient(wip) as client:
                map_dict.update({nm_ip: wip for nm_ip in
                                 client.namespace.list_namespaces_ips()})

        self.dump_workloads_vifs_map(map_dict)

    def set_workloads_vifs_map(self, workload_vif_map):
        """
        This function directly dumps workloads_vifs_map
        :param workload_vif_map:
        :return:
        """
        # TODO decide workload_vif_map pattern from the user
        self.dump_workloads_vifs_map(workload_vif_map)

    def load_workloads_vifs_map(self):
        log.info("Loading workloads_vifs map")
        with open(os.path.join(
                WORKLOAD_VIF_MAP_FILE_PATH, WORKLOAD_VIF_MAP_FILE), "rb") as wv_map:
            self.workload_vif_map = pickle.loads(wv_map.read())
            self.vif_map_load = True

    def dump_workloads_vifs_map(self, map_obj):
        if not os.path.isdir(WORKLOAD_VIF_MAP_FILE_PATH):
            os.makedirs(WORKLOAD_VIF_MAP_FILE_PATH)
        workload_vifs_file = os.path.join(WORKLOAD_VIF_MAP_FILE_PATH,
                                          WORKLOAD_VIF_MAP_FILE)
        os.remove(workload_vifs_file) if os.path.exists(workload_vifs_file) \
            else None
        log.info("Saving workloads_vifs map %r " % (workload_vifs_file))
        with open(workload_vifs_file, 'wb') as fd:
            pickle.dump(map_obj, fd)


class DataCenterTrafficController(TrafficController):
    """
    This TrafficController deals with On-prem traffic
    """
    def __init__(self, gateway_host=None, axon_server_port=5678):
        super(DataCenterTrafficController, self).__init__()
        self._axon_server_port = axon_server_port
        self._gw_host = gateway_host
        self._workload_servers = defaultdict(list)
        self.__map_obj = WorkloadVifsMap()
        self._servers = dict()
        self.__map_obj.load_workloads_vifs_map()

    def get_associated_workload(self, vif):
        if self.__map_obj.vif_map_load:
            return self.__map_obj.workload_vif_map.get(vif)

    def __create_rules(self, traffic_config):
        for trule in traffic_config:
            src_vif = str(trule.src_eps.ip_list[0])
            dst_vif = str(trule.dst_eps.ip_list[0])
            if not self._servers.get(str(src_vif)):
                self._servers[str(src_vif)] = TrafficRecord(src_vif)
            if not self._servers.get(str(dst_vif)):
                self._servers[str(dst_vif)] = TrafficRecord(dst_vif)
            self._servers[str(src_vif)].add_client(
                trule.protocol, trule.port.port,
                dst_vif, trule.connected,
                trule.action)
            self._servers[str(dst_vif)].add_server(
                trule.protocol, trule.port.port)

    def register_traffic(self, traffic_config):
        self.__create_rules(traffic_config)
        for vif, rule in list(self._servers.items()):
            workload = self.get_associated_workload(vif)
            workload = workload if workload else vif
            self._workload_servers[str(workload)].append(rule.as_dict())
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(workload_server, rule_list, self._gw_host, self._axon_server_port) for
                  workload_server, rule_list in
                  list(self._workload_servers.items())]
        pool.map(register_traffic, params)
        pool.close()
        pool.join()

    def unregister_traffic(self, traffic_config):
        pass

    def __stop_clients(self, servers):
        servers = servers if servers else list(self._workload_servers.keys())
        if not servers:
            return
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(server, self._gw_host, self._axon_server_port) for server in servers]
        pool.map(stop_clients, params)
        pool.close()
        pool.join()

    def __stop_servers(self, servers):
        servers = servers if servers else list(self._workload_servers.keys())
        if not servers:
            return
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(server, self._gw_host, self._axon_server_port) for server in servers]
        pool.map(stop_servers, params)
        pool.close()
        pool.join()

    def __start_servers(self, servers):
        servers = servers if servers else list(self._workload_servers.keys())
        if not servers:
            return
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(server, self._gw_host, self._axon_server_port) for server in servers]
        pool.map(start_servers, params)
        pool.close()
        pool.join()

    def __start_clients(self, servers):
        servers = servers if servers else list(self._workload_servers.keys())
        if not servers:
            return
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(server, self._gw_host, self._axon_server_port) for server in servers]
        pool.map(start_clients, params)
        pool.close()
        pool.join()

    def clear_all_traffic_rules(self, servers=None):
        servers = servers if servers else list(self._workload_servers.keys())
        if not servers:
            return
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(server, self._gw_host, self._axon_server_port) for server in servers]
        pool.map(clear_traffic_rules, params)
        pool.close()
        pool.join()

    def rediscover_namespaces(self, servers=None):
        servers = servers if servers else list(self._workload_servers.keys())
        if not servers:
            return
        pool = ThreadPool(THREADPOOL_SIZE)
        params = [(server, self._gw_host, self._axon_server_port) for server in servers]
        pool.map(rediscover_namespaces, params)
        pool.close()
        pool.join()

    def stop_traffic(self, servers=None):
        self.__stop_clients(servers)
        self.__stop_servers(servers)

    def start_traffic(self, servers=None):
        self.__start_servers(servers)
        self.__start_clients(servers)

    def restart_traffic(self, servers=None):
        self.stop_traffic(servers)
        self.start_traffic(servers)
