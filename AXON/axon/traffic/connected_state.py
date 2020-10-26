#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import abc
import logging
import six

from axon.db.sql.config import session_scope
from axon.db.sql.repository import Repositories


@six.add_metaclass(abc.ABCMeta)
class ConnectedState:

    @abc.abstractmethod
    def create_connected_state(self, endpoint, servers=None, clients=None):
        """Create connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        :param servers: list of (protocol, port) tuple
        :type servers: list
        :param clients: list of clients
        :type clients: list
        """
        pass

    @abc.abstractmethod
    def update_connected_state(self, endpoint, servers=None, clients=None):
        """Update connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        :param servers: list of (protocol, port) tuple
        :type servers: list
        :param clients: list of clients
        :type clients: list
        """
        pass

    @abc.abstractmethod
    def get_connected_state(self, endpoint=None):
        """Get connected state for an endpoint if specified
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        pass

    @abc.abstractmethod
    def get_servers(self, endpoint):
        """Get servers for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        pass

    @abc.abstractmethod
    def get_clients(self, endpoint):
        """Get Clients for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        pass

    @abc.abstractmethod
    def delete_connected_state(self, endpoint=None):
        """Delete connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        pass


class DBConnectedState(ConnectedState):
    """Stores the connected state in Relational Database"""
    def __init__(self):
        self._repository = Repositories()
        self.log = logging.getLogger(__name__)

    def update_connected_state(self, endpoint, servers=None, clients=None):
        """
        Update connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        :param servers: list of (protocol, port) tuple
        :type servers: list
        :param clients: list of clients
        :type clients: list
        """
        with session_scope() as session:
            self._repository.connected_state.update(
                session, endpoint, servers=servers, clients=clients)

    def create_connected_state(self, endpoint=None,
                               servers=None, clients=None):
        """Create connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        :param servers: list of (protocol, port) tuple
        :type servers: list
        :param clients: list of clients
        :type clients: list
        """
        with session_scope() as session:
            self._repository.create_connected_state(
                session, endpoint=endpoint,
                servers=servers, clients=clients)

    def get_connected_state(self, endpoint=None):
        """
        Get connected state for an endpoint if specified
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        with session_scope() as session:
            filters = {}
            if endpoint:
                filters['endpoint'] = endpoint
            return self._repository.connected_state.get_all(
                session, **filters)

    def delete_connected_state(self, endpoint=None):
        """
        Delete connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        with session_scope() as session:
            if endpoint:
                self._repository.connected_state.delete(session,
                                                        endpoint=endpoint)
            else:
                self._repository.connected_state.delete_all(session)
            session.commit()

    def get_servers(self, endpoint):
        """
        Get Servers for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        with session_scope() as session:
            return self._repository.connected_state.get_servers(
                session, endpoint)

    def get_clients(self, endpoint):
        """
        Get Clients for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        with session_scope() as session:
            return self._repository.connected_state.get_clients(
                session, endpoint)


class ConnectedStateProcessor(object):
    """Class to process the connected state"""

    def __init__(self, connected_state):
        """
        :param connected_state: connected state representation
        :type connected_state: object of DBConnectedState
        """
        self._connected_state = connected_state

    def __update_servers(self, current_servers, new_servers, op='add'):
        """
        update servers list
        """
        if op == 'add':
            servers = set(current_servers) | set(new_servers)
        else:
            servers = set(current_servers) - set(new_servers)
        return list(servers)

    def __update_clients(self, current_clients, new_clients, op='add'):
        """
        Update clients list
        """
        client_map = {
            (protocol, port, destination):
                (protocol, port, destination, connected, action) for
            protocol, port, destination, connected, action in current_clients}
        for protocol, port, destination, connected, action in new_clients:
            if op == 'add':
                client_map[(protocol, port, destination)] = (
                    protocol, port, destination, connected, action)
            else:
                client_map.pop((protocol, port, destination), None)

        return list(client_map.values())

    def create_or_update_connected_state(
            self, endpoint, servers=None, clients=None):
        """
        Create or update connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        :param servers: list of (protocol, port) tuple
        :type servers: list
        :param clients: list of clients
        :type clients: list
        """
        cs = self._connected_state.get_connected_state(endpoint)
        if not cs:
            self._connected_state.create_connected_state(
                endpoint, servers, clients)
        else:
            updated_servers = self.__update_servers(cs[0]['servers'], servers)
            updated_clients = self.__update_clients(cs[0]['clients'], clients)
            self._connected_state.update_connected_state(
                endpoint, updated_servers, updated_clients)

    def get_clients(self, endpoint):
        """
        Get Clients for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        return self._connected_state.get_clients(endpoint)

    def get_servers(self, endpoint):
        """
        Get Servers for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        return self._connected_state.get_servers(endpoint)

    def get_connected_state(self, endpoint=None):
        """
        Get connected state for an endpoint if specified
        :param endpoint: endpoint ip
        :type endpoint: str
        """
        return self._connected_state.get_connected_state(endpoint)

    def delete_connected_state(self, endpoint=None,
                               servers=None, clients=None):
        """
        Delete connected state for an endpoint
        :param endpoint: endpoint ip
        :type endpoint: str
        :param servers: servers to be deleted
        :type servers: list
        :param clients: clients to be deleted
        :type clients: list
        """
        if servers is None and clients is None:
            self._connected_state.delete_connected_state(endpoint)
        else:
            cs = self._connected_state.get_connected_state(endpoint)
            if cs:
                updated_servers = self.__update_servers(
                    cs[0]['servers'], servers, op='del')
                updated_clients = self.__update_clients(
                    cs[0]['clients'], clients, op='del')
                self._connected_state.update_connected_state(
                    endpoint, updated_servers, updated_clients)
