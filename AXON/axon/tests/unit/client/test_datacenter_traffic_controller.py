#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock

from axon.tests import base as test_base
from axon.client.traffic_elements import TrafficRule, \
    Endpoint, Port, Protocol, Action, Connected
from axon.client.datacenter_traffic_controller import \
    DataCenterTrafficController

rule_list = list()
rule_list.append(
    TrafficRule(Endpoint('1.2.3.4'), Endpoint('1.2.3.5'),
                Port(12345), Protocol.UDP, Connected.CONNECTED,
                Action.ALLOW)
)

workload_vif_map = {'1.2.3.4': '1.2.3.4', '1.2.3.5': '1.2.3.5'}


class TestDataCenterTrafficController(test_base.BaseTestCase):
    """
    Test for DataCenterTrafficController utilities
    """

    def setUp(self):
        super(TestDataCenterTrafficController, self).setUp()
        self._local_setup()

    @mock.patch('axon.client.datacenter_traffic_controller.WorkloadVifsMap')
    def _local_setup(self, mock_vif_map):
        mock_obj = mock_vif_map.return_value
        mock_obj.load_workloads_vifs_map.return_value = None
        mock_obj.workload_vif_map = workload_vif_map
        mock_obj.vif_map_load = True
        self.dc_traffic_controller = DataCenterTrafficController()

    @mock.patch('axon.client.axon_client.TrafficManger.register_traffic')
    @mock.patch('rpyc.connect')
    def test_register_traffic(self, mock_rpyc_conn, mock_register):
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        self.dc_traffic_controller.register_traffic(rule_list)
        mock_register.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.unregister_traffic')
    @mock.patch('rpyc.connect')
    def test_unregister_traffic(self, mock_rpyc_conn, mock_unregister):
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        self.dc_traffic_controller.unregister_traffic(rule_list)
        mock_unregister.assert_not_called()

    @mock.patch('axon.client.axon_client.TrafficManger.start_servers')
    def test_start_traffic_with_no_servers(self, mock_start):
        self.dc_traffic_controller.start_traffic()
        mock_start.assert_not_called()

    @mock.patch('axon.client.axon_client.TrafficManger.start_servers')
    @mock.patch('rpyc.connect')
    def test_start_traffic_with_servers(self, mock_rpyc_conn, mock_start):
        servers = ['1.2.3.4', '2.3.4.5']
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        mock_start.return_value = None
        self.dc_traffic_controller.start_traffic(servers=servers)
        mock_start.assert_called()

    @mock.patch('axon.client.axon_client.TrafficManger.stop_servers')
    def test_stop_traffic_with_no_servers(self, mock_stop):
        self.dc_traffic_controller.stop_traffic()
        mock_stop.assert_not_called()

    @mock.patch('axon.client.axon_client.TrafficManger.stop_servers')
    @mock.patch('rpyc.connect')
    def test_stop_traffic_with_servers(self, mock_rpyc_conn, mock_stop):
        servers = ['1.2.3.4', '2.3.4.5']
        rpyc_conn = mock_rpyc_conn.return_value
        rpyc_conn.root.return_value = None
        mock_stop.return_value = None
        self.dc_traffic_controller.stop_traffic(servers=servers)
        mock_stop.assert_called()

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
        self.dc_traffic_controller.restart_traffic(servers=servers)
        mock_start.assert_called()
