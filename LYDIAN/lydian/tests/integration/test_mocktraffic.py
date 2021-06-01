#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

# Run this test using following command.
#    python -m unittest discover -p test_mocktraffic.py lydian/tests/integration
'''
A simple test case for sending traffic.
'''

import logging
import queue
import uuid

from lydian.apps.mocktraffic import MockTraffic
from lydian.tests.integration.test_lydian import TrafficAppTest

log = logging.getLogger(__name__)


class MockTrafficTest(TrafficAppTest):
    DB_FILE = './test_mock_traffic_rules.db'
    MAX_QUEUE_SIZE = 20000

    DUMMY_RULE = {
        'reqid': '%s' % uuid.uuid4(),
        'ruleid': '%s' % uuid.uuid4(),
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'protocol': 'TCP',
        'port': 9468,
        'connected': True,
        'tool': 'mock'
    }

    def setUp(self):
        self.traffic_records = queue.Queue(self.MAX_QUEUE_SIZE)
        self.mocktraffic = MockTraffic(self.traffic_records)
        self.mocktraffic.start()
        self.traffic_tools = {'mock': self.mocktraffic}
        super(MockTrafficTest, self).setUp()
