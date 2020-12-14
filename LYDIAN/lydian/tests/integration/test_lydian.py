#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
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

from lydian.apps.rules import RulesApp
from lydian.apps.controller import TrafficControllerApp
from lydian.apps.results import Results
from lydian.apps.recorder import RecordManager
from lydian.apps.monitor import ResourceMonitor
from lydian.recorder.wf_client import WavefrontTrafficRecorder, WavefrontResourceRecorder
from lydian.utils.network_utils import NamespaceManager, InterfaceManager
from lydian.utils.logger import setup_logging

log = logging.getLogger(__name__)


class TrafficAppTest(unittest.TestCase):
    DB_FILE = './test_traffic_rules.db'
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
        setup_logging()
        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)

        # Traffic Records.
        self.traffic_records = queue.Queue(self.MAX_QUEUE_SIZE)
        # Resource records.
        self.resource_records = queue.Queue(self.MAX_QUEUE_SIZE)

        self.rulesApp = RulesApp(db_file=self.DB_FILE)
        self.controller = TrafficControllerApp(self.traffic_records, self.rulesApp)
        self.monitor = ResourceMonitor(self.resource_records)
        self.results = Results()

        self.db_pool = RecordManager(self.traffic_records, self.resource_records)

        self.db_pool.start()
        self.monitor.start()

    def test_traffic(self):
        rules = [('TCP', 9465), ('UDP', 9465), ('HTTP', 9466)]
        traffic_rules = []
        for protocol, port in rules:
            _rule = dict(self.DUMMY_RULE)
            # _rule['reqid'] =  '%s' % uuid.uuid4()
            _rule['ruleid'] = '%s' % uuid.uuid4()
            _rule['protocol'] = protocol
            _rule['port'] = port
            traffic_rules.append(_rule)

        reqid = self.DUMMY_RULE['reqid']
        self.controller.register_traffic(traffic_rules)
        time.sleep(6)  # Wait for taffic to run for 10 seconds.
        records = self.results.traffic(self.DUMMY_RULE['reqid'])
        assert records, "Traffic results missing"

        # Check for Start / Stop Traffic
        ruleid = traffic_rules[0]['ruleid']
        self.controller.stop(ruleid)
        time.sleep(10)
        # Ensure no traffic recorder in last 10 seconds.
        ts = int(time.time())
        records = self.results.traffic(reqid=reqid, ruleid=ruleid, timestamp=(ts-8, ts))
        assert not records, "Stop traffic not working..."
        self.controller.start(ruleid)

        # DEBUGGING TIPS
        # tcp_client = self.controller._client_mgr._traffic_tasks[ruleid]
        # tcp_client.stop()
        # time.sleep(3)   # time should be code update frequency
        # tcp_client.start()

    def tearDown(self):
        self.controller.close()
        self.db_pool.close()
        self.rulesApp.close()
        os.remove(self.DB_FILE)
