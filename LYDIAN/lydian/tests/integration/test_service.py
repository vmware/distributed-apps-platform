#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
A simple test case for sending traffic.
'''

import logging
import os
import queue
import time
import unittest
import uuid

from lydian.controller.rpyc_controller import LydianController
from lydian.controller.client import LydianClient

log = logging.getLogger(__name__)


class TrafficAppTest(unittest.TestCase):
    DB_FILE = 'test_traffic_rules.db'
    MAX_QUEUE_SIZE = 20000

    DUMMY_RULE = {
        'reqid': '%s' % uuid.uuid4(),
        'ruleid': '%s' % uuid.uuid4(),
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'protocol': 'TCP',
        'port': 9465,
        'connected': True
    }

    def setUp(self):
        self.service = LydianController()
        self.service.start()


    def test_traffic(self):
        traffic_rules = [self.DUMMY_RULE]

        with LydianClient('localhost') as client:
            client.controller.register_traffic(traffic_rules)
            time.sleep(2)  # Wait for taffic to run for 10 seconds.
            records = client.results.traffic(self.DUMMY_RULE['reqid'])
            assert records, "Traffic results missing"

    def tearDown(self):
        self.service.stop()
