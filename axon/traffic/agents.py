#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import ipaddress
import logging


from axon.traffic.connected_state import ConnectedStateProcessor, \
    DBConnectedState
from axon.traffic.manager import RootNsServerManager, NamespaceServerManager,\
    NamespaceClientManager, RootNsClientManager
from axon.utils.network_utils import NamespaceManager, InterfaceManager
import axon.common.config as axon_config


class AxonRootNamespaceServerAgent(object):
    """
    Launch Servers in Root Namespace
    """

    def __init__(self):
        self.mngrs_map = {}
        self.connected_state = ConnectedStateProcessor(DBConnectedState())
        self._primary_ep = None
        self._if_manager = InterfaceManager()
        self.log = logging.getLogger(__name__)

    @property
    def primary_endpoint(self):
        """
        Get the primary endpoint address from the DB
        It assumes in non namespace mode there will be
        only single interface.
        """
        if not self._primary_ep:
            endpoints = self.connected_state.get_connected_state()
            if endpoints:
                self._primary_ep = endpoints[0]['endpoint']
        return self._primary_ep

    def start_servers(self, namespace='root'):
        """
        Start Set of default servers
        :return: None
        """
        if not self.primary_endpoint:
            self.log.warning("Server will not be started since "
                             "no connected state exists yet")
            return
        src = self.primary_endpoint
        mngr = self.mngrs_map.get((namespace, src), RootNsServerManager())

        servers = self.connected_state.get_servers(src)
        servers = servers if servers else []
        for proto, port in servers:
            mngr.start_server(proto, port, src)
        self.mngrs_map[(namespace, src)] = mngr

    def stop_servers(self, namespace='root'):
        """
        Stop all Servers
        :return: None
        """
        for mngr in self.mngrs_map.values():
            mngr.stop_all_servers()

    def add_server(self, port, protocol, endpoint, namespace='root'):
        """
        Run a Server in a root namespace
        :param port: port on which server will listen
        :type port: int
        :param protocol: protocol on which server will listen
        :type protocol: str
        :return: None
        """
        interface = self._if_manager.get_interface_by_ip(endpoint)
        if not interface:
            self.log.error("No interface found with IP %s on host" % endpoint)
            return
        mngr = self.mngrs_map.get((namespace, endpoint), RootNsServerManager())
        mngr.start_server(protocol, port, endpoint)
        self.connected_state.create_or_update_connected_state(
            endpoint, [(protocol, port)], [])
        self.mngrs_map[(namespace, endpoint)] = mngr

    def list_servers(self):
        server_list = []
        for mngr in self.mngrs_map.values():
            server_list.extend(mngr.list_servers())
        return server_list

    def get_server(self, protocol, port):
        server_list = []
        for mngr in self.mngrs_map.values():
            server_list.extend(mngr.get_server(protocol, port))
        return server_list

    def stop_server(self, protocol, port, namespace='root', endpoint=None):
        ns_list = [namespace]
        endpoint = endpoint or self.primary_endpoint
        for (ns, src), mngr in self.mngrs_map.items():
            if ns not in ns_list:
                continue
            if src == endpoint:
                mngr.stop_server(port, protocol)
                break


class AxonNameSpaceServerAgent(AxonRootNamespaceServerAgent):
    """
    Launch Servers in different namespaces
    """

    def __init__(self, ns_list=None, ns_interface_map=None):
        super(AxonNameSpaceServerAgent, self).__init__()
        self._ns_list = ns_list
        self._ns_iterface_map = ns_interface_map
        self._setup()

    def _setup(self):
        if not self._ns_list or not self._ns_iterface_map:
            mngr = NamespaceManager()
            self._ns_list = mngr.get_all_namespaces()
            self._ns_iterface_map = mngr.get_namespace_interface_map()

    def start_servers(self, namespace=None):
        """
        Start a set of default server in given namespace
        :param namespace: namespace name
        :type namespace: str
        :return: None
        """
        ns_list = [namespace] if namespace else self._ns_list
        for ns in ns_list:
            interfaces = self._ns_iterface_map.get(ns)
            interfaces = [iface for iface in interfaces for prefix in
                          axon_config.NAMESPACE_INTERFACE_NAME_PREFIXES
                          if prefix in iface.name]
            if not interfaces:
                continue
            _servers = []
            for iface in interfaces:
                if _is_valid_ip(iface.address):
                    src = iface.address
                    _servers.append((src, self.connected_state.get_servers(src)))
            if not _servers:
                continue
            for src, proto_port in _servers:
                if not proto_port:
                    continue
                ns_mngr = self.mngrs_map.get((ns, src), NamespaceServerManager(ns))
                for proto, port in proto_port:
                    ns_mngr.start_server(proto, port, src)
                self.mngrs_map[(ns, src)] = ns_mngr

    def stop_servers(self, namespace=None):
        """
        Stop all server in given namespace
        :return: None
        """
        ns_list = [namespace] if namespace else self._ns_list
        for (ns, src), mngr in self.mngrs_map.items():
            if ns in ns_list:
                mngr.stop_all_servers()

    def add_server(self, port, protocol, endpoint, namespace=None):
        """
        Run a Server in a given namespace
        :param port: port on which server will listen
        :type port: int
        :param protocol: protocol on which server will listen
        :type protocol: str
        :param namespace: namespace name
        :type namespace: str
        :return: None
        """
        ns_list = [namespace] if namespace else self._ns_list
        for ns in ns_list:
            interfaces = self._ns_iterface_map.get(ns)
            interfaces = [iface for iface in interfaces for prefix in
                                 axon_config.NAMESPACE_INTERFACE_NAME_PREFIXES
                                 if prefix in iface.name]
            interfaces = [x for x in interfaces if x.address == endpoint]
            if not interfaces:
                continue
            src = endpoint
            ns_mngr = self.mngrs_map.get((ns, src), NamespaceServerManager(ns))
            ns_mngr.start_server(protocol, port, src)
            self.connected_state.create_or_update_connected_state(
                src, [(protocol, port)], [])
            self.mngrs_map[(ns, src)] = ns_mngr
            break
        else:
            self.log.error("Unable to add server since"
                           "there is no matching IP %s found in namespace %s" %
                           (endpoint, namespace))

    def stop_server(self, protocol, port, namespace=None, endpoint=None):
        ns_list = [namespace] if namespace else self._ns_list
        for (ns, src), mngr in self.mngrs_map.items():
            if ns not in ns_list:
                continue
            if not endpoint:
                mngr.stop_server(port, protocol)
            else:
                if src == endpoint:
                    mngr.stop_server(port, protocol)
                    break

    def rediscover_namespaces(self):
        self._ns_list, self._ns_iterface_map = None, None
        mngr = NamespaceManager()
        mngr.discover_namespaces()
        self._ns_list = mngr.get_all_namespaces()
        self._ns_iterface_map = mngr.get_namespace_interface_map()


class AxonRootNamespaceClientAgent(object):
    """
    Launch Servers in Root Namespace
    """
    def __init__(self, record_queue):
        self.mngrs_map = {}
        self.connected_state = ConnectedStateProcessor(DBConnectedState())
        self._primary_ep = None
        self._record_queue = record_queue
        self.log = logging.getLogger(__name__)

    # TODO(Pradeep Singh) MOve below code to a common location
    @property
    def primary_endpoint(self):
        """
        Get the primary endpoint address from the DB
        It assumes in non namespace mode there will be
        only single interface.
        """
        if not self._primary_ep:
            endpoints = self.connected_state.get_connected_state()
            if endpoints:
                self._primary_ep = endpoints[0]['endpoint']
        return self._primary_ep

    def start_clients(self, namespace='localhost'):
        if not self.primary_endpoint:
            self.log.warning("Clients will not be started since "
                             "no connected state exists yet")
            return
        clients = self.connected_state.get_clients(self.primary_endpoint)
        clients = clients if clients else []
        if clients:
            src = self.primary_endpoint
            mngr = self.mngrs_map.get((namespace, src), RootNsClientManager(self._record_queue))
            mngr.start_client(src, clients)
            self.mngrs_map[(namespace, src)] = mngr

    def stop_clients(self, namespace='localhost'):
        """
        Stop all Clients
        :return: None
        """
        for mngr in self.mngrs_map.values():
            mngr.stop_clients()

    def stop_client(self, namespace='localhost', endpoint=None):
        ns_list = [namespace]
        endpoint = endpoint or self.primary_endpoint
        for (ns, src), mngr in self.mngrs_map.items():
            if ns not in ns_list:
                continue
            if src == endpoint:
                mngr.stop_client()
                break


class AxonNameSpaceClientAgent(AxonRootNamespaceClientAgent):
    """
    Launch Servers in different namespaces
    """

    def __init__(self, record_queue, ns_list=None, ns_iterface_map=None):
        super(AxonNameSpaceClientAgent, self).__init__(record_queue)
        self._ns_list = ns_list
        self._ns_iterface_map = ns_iterface_map
        self._setup()

    def _setup(self):
        if not self._ns_list or not self._ns_iterface_map:
            mngr = NamespaceManager()
            self._ns_list = mngr.get_all_namespaces()
            self._ns_iterface_map = mngr.get_namespace_interface_map()

    def start_clients(self, namespace=None):
        ns_list = [namespace] if namespace else self._ns_list
        for ns in ns_list:
            interfaces = self._ns_iterface_map.get(ns)
            interfaces = [iface for iface in interfaces for prefix in
                          axon_config.NAMESPACE_INTERFACE_NAME_PREFIXES
                          if prefix in iface.name]
            if not interfaces:
                continue
            _clients = []
            for iface in interfaces:
                if _is_valid_ip(iface.address):
                    src = iface.address
                    _clients.append((src, self.connected_state.get_clients(src)))
            if not _clients:
                continue
            for src, clients in _clients:
                if not clients:
                    continue
                ns_mngr = self.mngrs_map.get((ns, src),
                                             NamespaceClientManager(ns, self._record_queue))
                ns_mngr.start_client(src, clients)
                self.mngrs_map[(ns, src)] = ns_mngr

    def stop_clients(self, namespace=None):
        ns_list = [namespace] if namespace else self._ns_list
        for (ns, src), mngr in self.mngrs_map.items():
            if ns in ns_list:
                mngr.stop_clients()

    def stop_client(self, namespace=None, endpoint=None):
        namespace = self._ns_iterface_map.get(namespace)
        if namespace:
            for (ns, src), mngr in self.mngrs_map.items():
                if ns not in namespace:
                    continue
                if not endpoint:
                    mngr.stop_client()
                else:
                    if endpoint == src:
                        mngr.stop_client()
                        break

    def rediscover_namespaces(self):
        self._ns_list, self._ns_iterface_map = None, None
        mngr = NamespaceManager()
        mngr.discover_namespaces()
        self._ns_list = mngr.get_all_namespaces()
        self._ns_iterface_map = mngr.get_namespace_interface_map()


def _is_valid_ip(ip_addr):

    try:
        if ipaddress.ip_address(ip_addr).version in (4, 6):
            return True
    except ValueError:
        return False
    return False
