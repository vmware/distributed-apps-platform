#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
This module implements the primary interface for Traffic Controller
system in scale framework. Any traffic controller in future, be it for
On prem, cloud or hybrid setup, it must adhere to this interface.
'''
import abc
import logging


class TrafficController(object):
    __metadata__ = abc.ABCMeta

    def __init__(self):
        self.log = logging.getLogger(__name__)

    @abc.abstractmethod
    def register_traffic(self, traffic_config):
        pass

    @abc.abstractmethod
    def unregister_traffic(self, traffic_config):
        pass

    @abc.abstractmethod
    def start_traffic(self):
        pass

    @abc.abstractmethod
    def stop_traffic(self):
        pass

    @abc.abstractmethod
    def restart_traffic(self):
        pass


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
