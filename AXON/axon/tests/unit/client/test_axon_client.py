#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock

from axon.tests import base as test_base
from axon.client.axon_client import AxonClient, TrafficManger,\
    StatsManager, NamespaceManager, InterfaceManager


class TestAxonClient(test_base.BaseTestCase):
    """
    Test for AxonClient utilities
    """

    def setUp(self):
        super(TestAxonClient, self).setUp()
        self.axon_host = '1.2.3.4'
        self.axon_port = 5678
        self.axon_proxy = '2.3.4.5'
        self.protocol = 'tcp'
        self.port = 12345
        self.endpoint = '3.4.5.6'
        self.ns = 'fake_ns'
        self.traffic_rules = 'fake_rules'
        self._local_setup()

    @mock.patch('rpyc.connect')
    def _local_setup(self, mock_rpyc):
        _client = AxonClient(axon_host=self.axon_host,
                             axon_port=self.axon_port)
        self.traffic = _client.traffic
        self.stats = _client.stats
        self.interface = _client.interface
        self.namespace = _client.namespace

    @mock.patch('rpyc.connect')
    def test_axon_client_init_without_proxy(self, mock_rpyc):
        conn = mock_rpyc.return_value
        conn.root.return_value = None
        _client = AxonClient(axon_host=self.axon_host,
                             axon_port=self.axon_port)
        self.assertTrue(isinstance(_client.traffic, TrafficManger))
        self.assertTrue(isinstance(_client.interface, InterfaceManager))
        self.assertTrue(isinstance(_client.stats, StatsManager))
        self.assertTrue(isinstance(_client.namespace, NamespaceManager))

    @mock.patch('rpyc.classic.connect')
    def test_axon_client_init_with_proxy(self, mock_rpyc):
        conn = mock_rpyc.return_value
        conn.root.return_value = None
        _client = AxonClient(axon_host=self.axon_host,
                             axon_port=self.axon_port,
                             proxy_host=self.axon_proxy)
        self.assertTrue(isinstance(_client.traffic, TrafficManger))
        self.assertTrue(isinstance(_client.interface, InterfaceManager))
        self.assertTrue(isinstance(_client.stats, StatsManager))
        self.assertTrue(isinstance(_client.namespace, NamespaceManager))

    def test_add_server(self):
        try:
            self.traffic.add_server(self.protocol,
                                    self.port,
                                    self.endpoint)
        except Exception:
            raise

    def test_start_clients(self):
        try:
            self.traffic.start_clients()
        except Exception:
            raise

    def test_get_traffic_rules(self):
        try:
            self.traffic.get_traffic_rules(self.endpoint)
        except Exception:
            raise

    def test_register_traffic(self):
        try:
            self.traffic.register_traffic(self.traffic_rules)
        except Exception:
            raise

    def test_unregister_traffic(self):
        try:
            self.traffic.unregister_traffic(self.traffic_rules)
        except Exception:
            raise

    def test_list_servers(self):
        try:
            return self.traffic.list_servers()
        except Exception:
            raise

    def test_get_server(self):
        try:
            return self.traffic.get_server(self.protocol, self.port)
        except Exception:
            raise

    def test_stop_servers(self):
        try:
            self.traffic.stop_servers(self.ns)
        except Exception:
            raise

    def test_start_servers(self):
        try:
            return self.traffic.start_servers(self.ns)
        except Exception:
            raise

    def test_stop_server(self):
        try:
            self.traffic.stop_server(self.protocol, self.port, self.ns)
        except Exception:
            raise

    def test_stop_client(self):
        src = 'fake_src'
        try:
            self.traffic.stop_client(src)
        except Exception:
            raise

    def test_stop_clients(self):
        try:
            self.traffic.stop_clients(self.ns)
        except Exception:
            raise

    def test_get_failure_count(self):
        try:
            self.stats.get_failure_count()
        except Exception:
            raise

    def test_get_success_count(self):
        try:
            self.stats.get_success_count()
        except Exception:
            raise

    def test_get_failures(self):
        try:
            self.stats.get_failures()
        except Exception:
            raise

    def test_list_namespaces(self):
        try:
            self.namespace.list_namespaces()
        except Exception:
            raise

    def test_get_namespace(self):
        try:
            self.namespace.get_namespace('fake_ns')
        except Exception:
            raise

    def test_list_namespaces_ips(self):
        try:
            self.namespace.list_namespaces_ips()
        except Exception:
            raise

    def test_list_interfaces(self):
        try:
            self.interface.list_interfaces()
        except Exception:
            raise

    def test_get_interface(self):
        try:
            self.interface.get_interface('fake_interface')
        except Exception:
            raise
