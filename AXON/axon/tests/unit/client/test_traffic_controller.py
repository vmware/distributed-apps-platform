#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from axon.tests import base as test_base
from axon.client.traffic_controller import TrafficRecord


class TestTrafficController(test_base.BaseTestCase):

    def setUp(self):
        super(TestTrafficController, self).setUp()
        self.traffic_record = TrafficRecord('1.2.3.4')

    def test_add_server(self):
        self.traffic_record.add_server('TCP', 12345)
        self.assertIn(('TCP', 12345),
                      self.traffic_record._servers)

    def test_add_client(self):
        self.traffic_record.add_client('TCP', 12345,
                                       '2.2.3.4',
                                       True, 'ALLOW')
        self.assertIn(('TCP', 12345, '2.2.3.4', True, 'ALLOW'),
                      self.traffic_record._clients)

    def test_as_dict(self):
        resp = self.traffic_record.as_dict()
        self.assertIn('servers', list(resp.keys()))
        self.assertIn('endpoint', list(resp.keys()))
        self.assertIn('clients', list(resp.keys()))
