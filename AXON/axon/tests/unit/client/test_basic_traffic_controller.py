#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock

from axon.tests import base as test_base
from axon.client.traffic_elements import TrafficRule, \
    Endpoint, Port, Protocol, Action, Connected
from axon.client.basic_traffic_controller import BasicTrafficController


rule_list = list()
rule_list.append(
    TrafficRule(Endpoint('1.2.3.4'), Endpoint('1.2.3.5'),
                Port(12345), Protocol.UDP, Connected.CONNECTED,
                Action.ALLOW)
)


class TestBasicTrafficController(test_base.BaseTestCase):
    """
    Test for Basic Traffic Controller utilities
    """
    def setUp(self):
        super(TestBasicTrafficController, self).setUp()
        self.traffic_controller = BasicTrafficController()

    @mock.patch('axon.client.axon_client.TrafficManger.register_traffic')
    @mock.patch('rpyc.connect')
    def test_register_traffic(self, mock_rpyc_conn, mock_register):
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        self.traffic_controller.register_traffic(rule_list)
        mock_register.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.register_traffic')
    @mock.patch('rpyc.connect')
    def test_register_traffic_with_exception(self,
                                             mock_rpyc_conn,
                                             mock_register):
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        mock_register.side_effect = Exception
        self.traffic_controller.register_traffic(rule_list)
        mock_register.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.unregister_traffic')
    @mock.patch('rpyc.connect')
    def test_unregister_traffic(self, mock_rpyc_conn, mock_unregister):
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        self.traffic_controller.unregister_traffic(rule_list)
        mock_unregister.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.unregister_traffic')
    @mock.patch('rpyc.connect')
    def test_unregister_traffic_with_exception(self,
                                               mock_rpyc_conn,
                                               mock_unregister):
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.side_effect = None
        mock_unregister.side_effect = Exception
        self.traffic_controller.unregister_traffic(rule_list)
        mock_unregister.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.start_servers')
    def test_start_traffic_with_no_servers(self, mock_start):
        self.traffic_controller.start_traffic()
        mock_start.assert_not_called()

    @mock.patch('axon.client.axon_client.TrafficManger.start_servers')
    @mock.patch('rpyc.connect')
    def test_start_traffic_with_servers(self,
                                        mock_rpyc_conn,
                                        mock_start):
        servers = ['1.2.3.4', '2.3.4.5']
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        mock_start.return_value = None
        self.traffic_controller.start_traffic(servers=servers)
        mock_start.assert_called()

    @mock.patch('axon.client.utils.ParallelWork.Do')
    def test_start_traffic_with_all_failed(self, mock_worker):
        servers = ['1.2.3.4', '2.3.4.5']
        mock_worker.return_value = [False, False, False]
        self.traffic_controller.start_traffic(servers=servers)
        mock_worker.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.stop_servers')
    def test_stop_traffic_with_no_servers(self, mock_stop):
        self.traffic_controller.stop_traffic()
        mock_stop.assert_not_called()

    @mock.patch('axon.client.axon_client.TrafficManger.stop_servers')
    @mock.patch('rpyc.connect')
    def test_stop_traffic_with_servers(self, mock_rpyc_conn, mock_stop):
        servers = ['1.2.3.4', '2.3.4.5']
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        mock_stop.return_value = None
        self.traffic_controller.stop_traffic(servers=servers)
        mock_stop.assert_called()

    @mock.patch('axon.client.utils.ParallelWork.Do')
    def test_stop_traffic_with_all_failed(self, mock_worker):
        servers = ['1.2.3.4', '2.3.4.5']
        mock_worker.return_value = [False, False, False]
        self.traffic_controller.stop_traffic(servers=servers)
        mock_worker.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.stop_servers')
    @mock.patch('axon.client.axon_client.TrafficManger.start_servers')
    @mock.patch('rpyc.connect')
    def test_restart_traffic_with_servers(self, mock_rpyc_conn,
                                          mock_start, mock_stop):
        servers = ['1.2.3.4', '2.3.4.5']
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        mock_start.return_value = None
        mock_stop.return_value = None
        self.traffic_controller.restart_traffic(servers=servers)
        mock_start.assert_called()
