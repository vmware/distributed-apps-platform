#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import abc
from collections import defaultdict
import logging
import six
import platform
import threading
if "Linux" in platform.uname():  # noqa
    from axon.utils import nsenter

from axon.traffic.servers import create_server_class
from axon.traffic.workers import WorkerProcess
from axon.traffic.clients import TrafficClient


class ServerRegistry(object):
    """
    Registry to holds all of the servers running across various namespaces
    """
    def __init__(self):
        self.__registry = defaultdict(dict)
        self.lock = threading.RLock()

    def add_server(self, namespace, port, protocol, server_obj):
        """
        Add server to registry
        :param namespace: name space where the server is running
        :type namespace: str
        :param port: port on which server is listening
        :type port: number
        :param protocol: protocol on which server is working
        :type protocol: str
        :param server_obj: server_obj, i.e. the server container object
        :type server_obj: ServerContainer
        :return: None
        """
        with self.lock:
            self.__registry[namespace][(port, protocol)] = server_obj

    def remove_server(self, namespace, port, protocol):
        """
        Remove server from registry
        :param namespace: name space where the server is running
        :type namespace: str
        :param port: port on which server is listening
        :type port: number
        :param protocol: protocol on which server is working
        :type protocol: str
        :return: None
        """
        with self.lock:
            if self.__registry[namespace].get((port, protocol)):
                del self.__registry[namespace][(port, protocol)]

    def get_server(self, namespace, port, protocol):
        """
        Get server from registry
        :param namespace: name space where the server is running
        :type namespace: str
        :param port: port on which server is listening
        :type port: number
        :param protocol: protocol on which server is working
        :type protocol: str
        :return: Server Object
        """
        with self.lock:
            return self.__registry[namespace].get((port, protocol))

    def get_all_servers(self):
        """
        Get all server objects
        """
        with self.lock:
            return list(self.__registry.items())


class ClientRegistry(object):
    """
    Registry to holds all of the clients running across various namespaces
    """
    def __init__(self):
        self.__registry = {}
        self.lock = threading.RLock()

    def add_client(self, namespace, client_obj):
        """
        Add client to registry
        :param namespace: name space where the client is running
        :type namespace: str
        :param client_obj: client container
        """
        with self.lock:
            self.__registry[namespace] = client_obj

    def remove_client(self, namespace):
        """
        Add client to registry
        :param namespace: name space where the client is running
        :type namespace: str
        """
        with self.lock:
            try:
                del self.__registry[namespace]
            except KeyError:
                pass

    def get_client(self, namespace):
        """
        Get A client object from registry
        :param namespace: namespace in which client is running
        :type namespace: str
        :param src: src ip on which client is bound to
        :type src: str
        :return: Client object
        :rtype: TrafficClient
        """
        with self.lock:
            return self.__registry.get(namespace)

    def get_all_client(self):
        """
        Get all client objects
        """
        with self.lock:
            return list(self.__registry.items())


@six.add_metaclass(abc.ABCMeta)
class ServerManager(object):
    """
    A class to manage servers
    """

    @abc.abstractmethod
    def start_server(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def stop_server(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def stop_all_servers(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def list_servers(self):
        pass

    @abc.abstractmethod
    def get_server(self, *args, **kwargs):
        pass


class RootNsServerManager(ServerManager):
    """
    Class which manages the servers in root NameSpace
    """

    ROOT_NAMESPACE_NAME = 'localhost'

    def __init__(self):
        self._server_registry = ServerRegistry()
        self.log = logging.getLogger(__name__)

    def start_server(self, protocol, port, src="0.0.0.0"):
        server_process = self._server_registry.get_server(
            self.ROOT_NAMESPACE_NAME, port, protocol)
        if server_process and server_process.is_running():
            self.log.warning("%s server on port %s is already running" %
                             (protocol, port))
            return
        self.log.info(
            "Starting %s server on port %s on interface %s" %
            (protocol, port, src))
        try:
            server_cls, args, kwargs = create_server_class(protocol, port, src)
            process = WorkerProcess(server_cls, args, kwargs)
            process.start()
            self._server_registry.add_server(
                self.ROOT_NAMESPACE_NAME, port, protocol, process)
        except Exception as e:
            self.log.exception(
                "Starting %s server on port %s on interface %s failed" %
                (protocol, port, src))
            raise e

    def stop_server(self, port, protocol):
        self.log.info(
            "Stopping %s server on port %s" % (protocol, port))
        try:
            server_process = self._server_registry.get_server(
                self.ROOT_NAMESPACE_NAME, port, protocol)
            if server_process and server_process.is_running():
                server_process.stop()
                self._server_registry.remove_server(
                    self.ROOT_NAMESPACE_NAME, port, protocol)
            elif server_process and not server_process.is_running():
                self.log.warning("%s server is not running on %s" %
                                 (protocol, port))
                self._server_registry.remove_server(
                    self.ROOT_NAMESPACE_NAME, port, protocol)
            else:
                self.log.warning("%s server is not running on %s" %
                                 (protocol, port))
        except Exception as e:
            self.log.exception(
                "Stopping %s server on port %s failed" % (protocol, port))
            raise e

    def stop_all_servers(self):
        servers = [(conf, server) for ns, conf_server_map in
                   self._server_registry.get_all_servers() for
                   conf, server in list(conf_server_map.items())]
        for conf, server in servers:
            self.log.info(
                "Stopping %s server on port %s" % (conf[1], conf[0]))
            try:
                if server.is_running():
                    server.stop()
                    self._server_registry.remove_server(
                        self.ROOT_NAMESPACE_NAME, conf[0], conf[1])
                else:
                    self.log.warning("%s server is not running on %s" %
                                     (conf[1], conf[0]))
                    self._server_registry.remove_server(
                        self.ROOT_NAMESPACE_NAME, conf[0], conf[1])
            except Exception:
                self.log.exception(
                    "Stopping %s server on port %s failed" %
                    (conf[1], conf[0]))

    def list_servers(self):
        servers = [(ns, conf) for ns, conf_server_map in
                   self._server_registry.get_all_servers() for
                   conf, server in list(conf_server_map.items())]
        return servers

    def get_server(self, protocol, port, namespace=None):
        servers = [(ns, conf) for ns, conf_server_map in
                   self._server_registry.get_all_servers() for
                   conf, server in list(conf_server_map.items()) if
                   conf[0] == port and conf[1] == protocol]
        return servers


class NamespaceServerManager(RootNsServerManager):
    """
    Class which manages servers in a Given Namespace
    """
    NAMESPACE_PATH = '/var/run/netns/'

    def __init__(self, namespace):
        super(NamespaceServerManager, self).__init__()
        self._ns = namespace
        self._ns_full_path = self.NAMESPACE_PATH + self._ns

    def start_server(self, protocol, port, src="0.0.0.0"):
        server_process = self._server_registry.get_server(
            self._ns, port, protocol)
        if server_process and server_process.is_running():
            self.log.warning("%s server on port %s is already running" %
                             (protocol, port))
            return
        self.log.info(
            "Starting %s server on port %s on interface %s in namespace %s" %
            (protocol, port, src, self._ns))
        try:
            server_cls, args, kwargs = create_server_class(protocol, port, src)
            process = WorkerProcess(server_cls, args, kwargs)
            with nsenter.namespace(self._ns_full_path, 'net'):
                process.start()
            self._server_registry.add_server(
                self._ns, port, protocol, process)
        except Exception as e:
            self.log.exception(
                "Starting %s server on port %s on interface %s failed" %
                (protocol, port, src))
            raise e

    def stop_server(self, port, protocol):
        try:
            server_process = self._server_registry.get_server(
                self._ns, port, protocol)
            self.log.info(
                "Stop %s server on port %s in namespace %s" %
                (protocol, port, self._ns))
            if server_process and server_process.is_running():
                with nsenter.namespace(self._ns_full_path, 'net'):
                    server_process.stop()
                    self._server_registry.remove_server(
                        self._ns, port, protocol)
            elif server_process and not server_process.is_running():
                self.log.warning("%s server is not running on %s" %
                                 (protocol, port))
                self._server_registry.remove_server(
                    self.ROOT_NAMESPACE_NAME, port, protocol)
            else:
                self.log.warning("%s server is not running on %s" %
                                 (protocol, port))
        except Exception as e:
            self.log.exception(
                "Stopping %s server on port %s failed in namespace %s" %
                (protocol, port, self._ns))
            raise e


@six.add_metaclass(abc.ABCMeta)
class ClientManager(object):
    """
    Class to manage Clients
    """

    @abc.abstractmethod
    def start_client(self, *args, **kwargs):
        """
        Start a Client
        """
        pass

    @abc.abstractmethod
    def stop_client(self, *args, **kwargs):
        """
        Stop a client
        """
        pass

    @abc.abstractmethod
    def stop_clients(self, *args, **kwargs):
        """
        Stop all Clients
        """
        pass


class RootNsClientManager(ClientManager):
    """
    Class which manages the clients in root NameSpace
    """

    ROOT_NAMESPACE_NAME = 'localhost'

    def __init__(self, record_queue):
        self._client_registry = ClientRegistry()
        self.log = logging.getLogger(__name__)
        self._record_queue = record_queue

    def start_client(self, src, clients):
        self.log.info("Starting client process on interface %s" % src)
        client = self._client_registry.get_client(self.ROOT_NAMESPACE_NAME)
        if client and client.is_running():
            self.log.warning("Client is already running on %s" % src)
            return
        try:
            process = WorkerProcess(
                TrafficClient, (src, clients, self._record_queue), {})
            process.start()
            self._client_registry.add_client(self.ROOT_NAMESPACE_NAME, process)
        except Exception as e:
            self.log.exception(
                "Starting client process on interface %s failed" % src)
            raise e

    def stop_client(self):
        self.log.info("Stopping client process")
        client = self._client_registry.get_client(self.ROOT_NAMESPACE_NAME)
        try:
            if client and client.is_running():
                client.stop()
                self._client_registry.remove_client(self.ROOT_NAMESPACE_NAME)
            elif client and not client.is_running():
                self.log.warning("Client is not running in root namespace")
                self._client_registry.remove_client(self.ROOT_NAMESPACE_NAME)
            else:
                self.log.warning("Client is not running in root namespace")
        except Exception:
            self.log.exception(
                "Stopping client failed in namespace %s" %
                self.ROOT_NAMESPACE_NAME)

    def stop_clients(self):
        self.log.info("Stopping all client processes")
        clients = [(client, namespace) for namespace, client in
                   self._client_registry.get_all_client()]

        for client, namespace in clients:
            try:
                client.stop()
                self._client_registry.remove_client(namespace)
            except Exception:
                self.log.exception("Stopping client failed in namespace %s" %
                                   self.ROOT_NAMESPACE_NAME)


class NamespaceClientManager(RootNsClientManager):
    """
    Class which manages Clients in a Given Namespace
    """

    NAMESPACE_PATH = '/var/run/netns/'

    def __init__(self, namespace, record_queue):
        super(NamespaceClientManager, self).__init__(record_queue)
        self._ns = namespace
        self._ns_full_path = self.NAMESPACE_PATH + self._ns

    def start_client(self, src, clients):
        client = self._client_registry.get_client(self._ns)
        if client and client.is_running():
            self.log.warning("Client is already running on %s" % src)
            return
        try:
            process = WorkerProcess(
                TrafficClient, (src, clients, self._record_queue), {})
            with nsenter.namespace(self._ns_full_path, 'net'):
                process.start()
                self._client_registry.add_client(self._ns, process)
        except Exception as e:
            self.log.exception(
                "Starting client process on interface %s failed" % src)
            raise e

    def stop_client(self):
        try:
            client = self._client_registry.get_client(self._ns)
            if client and client.is_running():
                with nsenter.namespace(self._ns_full_path, 'net'):
                    client.stop()
                    self._client_registry.remove_client(self._ns)
            elif client and not client.is_running():
                self.log.warning("Client is not running in namespace %s" %
                                 self._ns)
                self._client_registry.remove_client(self._ns)
            else:
                self.log.warning("Client is not running in namespace %s" %
                                 self._ns)
        except Exception:
            self.log.exception("Stopping client failed in namespace %s" %
                               self._ns)
