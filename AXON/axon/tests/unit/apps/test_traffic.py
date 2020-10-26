# !/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from axon.common import config as conf
import mock

from axon.tests import base as test_base
from axon.apps.traffic import TrafficApp
from axon.traffic.connected_state import ConnectedStateProcessor


class TestTrafficApp(test_base.BaseTestCase):
    """
    Test for TrafficApp utilities
    """

    def setUp(self):
        super(TestTrafficApp, self).setUp()
        self._traffic_app = TrafficApp(conf)

    @mock.patch('axon.traffic.agents.AxonRootNamespaceServerAgent.'
                'add_server')
    def test_add_server(self, mock_agent):
        protocol = 'tcp'
        port = 12345
        endpoint = '1.2.3.4'
        namespace = None
        self._traffic_app.add_server(protocol, port, endpoint, namespace)
        mock_agent.assert_called_with(12345, 'tcp', '1.2.3.4', None)

    def test_add_server_in_no_ns(self):
        protocol = 'tcp'
        port = 12345
        endpoint = '1.2.3.4'
        namespace = 'fake_ns'
        self.assertRaises(ValueError, self._traffic_app.add_server,
                          protocol, port, endpoint, namespace)

    @mock.patch('axon.traffic.agents.AxonRootNamespaceServerAgent.'
                'list_servers')
    def test_list_servers(self, mock_agent):
        self._traffic_app.list_servers()
        mock_agent.assert_called()

    @mock.patch('axon.traffic.agents.AxonRootNamespaceServerAgent.'
                'get_server')
    def test_get_server(self, mock_get):
        mock_get.return_value = 'fake_server'
        server = self._traffic_app.get_server('TCP', '12345')
        mock_get.assert_called_with('TCP', '12345')
        self.assertEqual(server, 'fake_server')

    @mock.patch('axon.traffic.agents.AxonRootNamespaceServerAgent.'
                'stop_servers')
    def test_stop_servers(self, mock_stop):
        self._traffic_app.stop_servers()
        mock_stop.assert_called()

    def test_stop_servers_in_no_ns(self):
        self.assertRaises(ValueError,
                          self._traffic_app.stop_servers, namespace='fake_ns')

    @mock.patch('axon.traffic.agents.AxonRootNamespaceServerAgent.'
                'start_servers')
    def test_start_servers(self, mock_start):
        self._traffic_app.start_servers()
        mock_start.assert_called()

    def test_start_servers_in_no_ns(self):
        self.assertRaises(ValueError,
                          self._traffic_app.start_servers,
                          namespace='fake_ns')

    @mock.patch('axon.traffic.agents.AxonRootNamespaceServerAgent.'
                'stop_server')
    def test_stop_server(self, mock_stop):
        self._traffic_app.stop_server('tcp', 12345)
        mock_stop.assert_called_with('tcp', 12345, None)

    def test_stop_server_in_no_ns(self):
        self.assertRaises(ValueError,
                          self._traffic_app.stop_server,
                          'tcp', 12345, namespace='fake_ns')

    @mock.patch('axon.traffic.agents.AxonRootNamespaceClientAgent.'
                'stop_client')
    def test_stop_client(self, mock_stop):
        self._traffic_app.stop_client()
        mock_stop.assert_called()

    def test_stop_client_in_no_ns(self):
        self.assertRaises(ValueError,
                          self._traffic_app.stop_client,
                          namespace='fake_ns')

    @mock.patch('axon.traffic.agents.AxonRootNamespaceClientAgent.'
                'stop_clients')
    def test_stop_clients(self, mock_stop):
        self._traffic_app.stop_clients()
        mock_stop.assert_called()

    def test_stop_clients_in_no_ns(self):
        self.assertRaises(ValueError,
                          self._traffic_app.stop_clients,
                          namespace='fake_ns')

    @mock.patch('axon.traffic.agents.AxonRootNamespaceClientAgent.'
                'start_clients')
    def test_start_clients(self, mock_start):
        self._traffic_app.start_clients()
        mock_start.assert_called()

    @mock.patch.object(ConnectedStateProcessor,
                       'create_or_update_connected_state')
    def test_register_traffic(self, mock_db_conn):
        traffic_config = [{'endpoint': '1.2.3.4',
                           'servers': ['1.2.3.4'],
                           'clients': ['2.3.4.5']}]
        self._traffic_app.register_traffic(traffic_config)
        mock_db_conn.assert_called_once_with('1.2.3.4',
                                             ['1.2.3.4'],
                                             ['2.3.4.5'])

    @mock.patch.object(ConnectedStateProcessor, 'delete_connected_state')
    def test_unregister_traffic(self, mock_db_conn):
        traffic_config = [{'endpoint': '1.2.3.4',
                           'servers': ['1.2.3.4'],
                           'clients': ['2.3.4.5']}]
        self._traffic_app.unregister_traffic(traffic_config)
        mock_db_conn.assert_called_once_with('1.2.3.4',
                                             ['1.2.3.4'],
                                             ['2.3.4.5'])

    @mock.patch.object(ConnectedStateProcessor, 'get_connected_state')
    def test_get_traffic_rules(self, mock_db_conn):
        mock_db_conn.return_value = {'1.2.3.4': ['fake_list']}
        traffic_config = self._traffic_app.get_traffic_rules('1.2.3.4')
        mock_db_conn.assert_called_once_with('1.2.3.4')
        self.assertEqual(traffic_config, {'1.2.3.4': ['fake_list']})


class TestTrafficAppNonNs(test_base.BaseTestCase):

    def setUp(self):
        super(TestTrafficAppNonNs, self).setUp()
        self._local_init()

    @mock.patch('axon.utils.network_utils.NamespaceManager.'
                'get_all_namespaces')
    def _local_init(self, mock_ns):
        mock_ns.return_value = ['fake_ns']
        conf.NAMESPACE_MODE = True
        self._traffic_app = TrafficApp(conf)

    @mock.patch('axon.traffic.agents.AxonNameSpaceServerAgent.'
                'add_server')
    def test_add_server(self, mock_agent):
        protocol = 'tcp'
        port = 12345
        endpoint = '1.2.3.4'
        namespace = 'fake_ns'
        self._traffic_app.add_server(protocol, port, endpoint, namespace)
        mock_agent.assert_called_with(12345, 'tcp', '1.2.3.4', 'fake_ns')

    @mock.patch('axon.traffic.agents.AxonNameSpaceServerAgent.list_servers')
    def test_list_servers(self, mock_agent):
        self._traffic_app.list_servers()
        mock_agent.assert_called()

    @mock.patch('axon.traffic.agents.AxonNameSpaceServerAgent.get_server')
    def test_get_server(self, mock_get):
        mock_get.return_value = 'fake_server'
        server = self._traffic_app.get_server('TCP', '12345')
        mock_get.assert_called_with('TCP', '12345')
        self.assertEqual(server, 'fake_server')

    @mock.patch('axon.traffic.agents.AxonNameSpaceServerAgent.stop_servers')
    def test_stop_servers(self, mock_stop):
        self._traffic_app.stop_servers(namespace='fake_ns')
        mock_stop.assert_called()

    @mock.patch('axon.traffic.agents.AxonNameSpaceServerAgent.start_servers')
    def test_start_servers(self, mock_start):
        self._traffic_app.start_servers(namespace='fake_ns')
        mock_start.assert_called()

    @mock.patch('axon.traffic.agents.AxonNameSpaceServerAgent.stop_server')
    def test_stop_server(self, mock_stop):
        self._traffic_app.stop_server('tcp', 12345, 'fake_ns')
        mock_stop.assert_called_with('tcp', 12345, 'fake_ns')

    @mock.patch('axon.traffic.agents.AxonNameSpaceClientAgent.stop_client')
    def test_stop_client(self, mock_stop):
        self._traffic_app.stop_client()
        mock_stop.assert_called()

    @mock.patch('axon.traffic.agents.AxonNameSpaceClientAgent.stop_clients')
    def test_stop_clients(self, mock_stop):
        self._traffic_app.stop_clients(namespace='fake_ns')
        mock_stop.assert_called()

    @mock.patch('axon.traffic.agents.AxonNameSpaceClientAgent.start_clients')
    def test_start_clients(self, mock_start):
        self._traffic_app.start_clients()
        mock_start.assert_called()
