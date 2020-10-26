#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock

from axon.tests import base as test_base
from axon.traffic.manager import RootNsServerManager, NamespaceServerManager
from axon.utils.network_utils import Interface
from axon.traffic.connected_state import ConnectedStateProcessor

CONNECTED_STATE = [{'endpoint': '1.2.3.4',
                    'servers': [('TCP', 12345), ('UDP', 12345)],
                    'clients': [('TCP', 12345, '1.2.3.5', True, 1)]}]
INTERFACE = Interface('veth-fake', '1.2.3.4', 2, None, None)


class TestAxonRootNamespaceServerAgent(test_base.BaseTestCase):
    """
    Test for AxonRootNamespaceServerAgent utilities
    """

    def setUp(self):
        super(TestAxonRootNamespaceServerAgent, self).setUp()
        self.local_setup()

    @mock.patch('axon.utils.network_utils.InterfaceManager')
    @mock.patch('axon.traffic.connected_state.ConnectedStateProcessor')
    def local_setup(self, mock_conn_state, mock_if_mngr):
        self.connected_state = mock_conn_state.return_value
        self.interface_manager = mock_if_mngr.return_value

        self.connected_state.get_connected_state.return_value =\
            CONNECTED_STATE
        self.connected_state.get_servers.return_value =\
            CONNECTED_STATE[0]['servers']

        self.interface_manager.get_interface_by_ip.side_effect =\
            'fake-interface'

        from axon.traffic.agents import AxonRootNamespaceServerAgent
        self.server_agent = AxonRootNamespaceServerAgent()
        self.server_agent.mngrs_map = {'root': RootNsServerManager()}

    @mock.patch.object(ConnectedStateProcessor, 'get_servers')
    @mock.patch.object(ConnectedStateProcessor,
                       'get_connected_state')
    @mock.patch('axon.traffic.manager.RootNsServerManager.start_server')
    def test_start_servers(self, mock_start, mock_conn_stat, mock_get_servers):
        mock_conn_stat.return_value = CONNECTED_STATE
        mock_get_servers.return_value = CONNECTED_STATE[0]['servers']
        self.server_agent.start_servers()
        mock_start.assert_called()

    @mock.patch('axon.traffic.manager.RootNsServerManager.stop_all_servers')
    def test_stop_servers(self, mock_stop):
        self.server_agent.stop_servers()
        mock_stop.assert_called()

    @mock.patch.object(ConnectedStateProcessor,
                       'create_or_update_connected_state')
    @mock.patch('axon.utils.network_utils.InterfaceManager.'
                'get_interface_by_ip')
    @mock.patch('axon.traffic.manager.RootNsServerManager.start_server')
    def test_add_server(self, mock_start, mock_get_if, mock_conn_stat):
        mock_get_if.return_value = INTERFACE
        mock_conn_stat.return_value = None
        self.server_agent.add_server(12345, 'TCP', '1.2.3.4')
        mock_start.assert_called()

    def test_list_servers(self):
        self.server_agent.list_servers()

    @mock.patch('axon.traffic.manager.RootNsServerManager.get_server')
    def test_get_server(self, mock_get_server):
        self.server_agent.get_server('TCP', 12345)
        mock_get_server.assert_called_with('TCP', 12345)

    @mock.patch('axon.traffic.manager.RootNsServerManager.stop_server')
    def test_stop_server(self, mock_stop_server):
        self.server_agent.stop_server('TCP', 12345)
        mock_stop_server.assert_called_with(12345, 'TCP')


class TestAxonNameSpaceServerAgent(test_base.BaseTestCase):

    def setUp(self):
        super(TestAxonNameSpaceServerAgent, self).setUp()
        self.local_setup()

    @mock.patch('axon.utils.network_utils.NamespaceManager')
    @mock.patch('axon.utils.network_utils.InterfaceManager')
    @mock.patch('axon.traffic.connected_state.ConnectedStateProcessor')
    def local_setup(self, mock_conn_state, mock_if_mngr, mock_ns_mngr):
        self.connected_state = mock_conn_state.return_value
        self.interface_manager = mock_if_mngr.return_value
        self.namespace_manager = mock_ns_mngr.return_value

        self.connected_state.get_connected_state.return_value =\
            CONNECTED_STATE
        self.connected_state.get_servers.return_value =\
            CONNECTED_STATE[0]['servers']

        self.interface_manager.get_interface_by_ip.side_effect =\
            'fake-interface'

        self.namespace_manager.get_all_namespaces.return_value = ['root']
        self.namespace_manager.get_namespace_interface_map = {
            'root': [INTERFACE]}

        from axon.traffic.agents import AxonNameSpaceServerAgent
        self.server_agent = AxonNameSpaceServerAgent(
            ns_list=['root'], ns_interface_map={'root': [INTERFACE]})
        self.server_agent.mngrs_map = {
            'root': NamespaceServerManager(namespace='root')}

    @mock.patch.object(ConnectedStateProcessor,
                       'get_servers')
    @mock.patch('axon.traffic.manager.NamespaceServerManager.start_server')
    def test_start_servers(self, mock_start, mock_get_servers):
        mock_get_servers.return_value = CONNECTED_STATE[0]['servers']
        self.server_agent.start_servers()
        mock_start.assert_called()

    @mock.patch('axon.traffic.manager.NamespaceServerManager.'
                'stop_all_servers')
    def test_stop_servers(self, mock_stop):
        self.server_agent.stop_servers()
        mock_stop.assert_called()

    @mock.patch.object(ConnectedStateProcessor,
                       'create_or_update_connected_state')
    @mock.patch('axon.traffic.manager.NamespaceServerManager.start_server')
    def test_add_server(self, mock_start, mock_conn_state):
        mock_conn_state.return_value = None
        self.server_agent.add_server(12345, 'TCP', '1.2.3.4')
        mock_start.assert_called()

    @mock.patch('axon.traffic.manager.NamespaceServerManager.stop_server')
    def test_stop_server(self, mock_stop_server):
        self.server_agent.stop_server('TCP', 12345)
        mock_stop_server.assert_called_with(12345, 'TCP')
