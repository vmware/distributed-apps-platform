#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

# Run this test using following command.
#    python -m unittest discover -p test_lydian.py lydian/tests/integration
'''
A simple test case for sending traffic.
'''

import logging
import os
import pickle
import queue
import time
import unittest
import uuid

from lydian.apps.monitor import ResourceMonitor
from lydian.apps.rules import RulesApp
from lydian.apps.recorder import RecordManager
from lydian.apps.results import Results
from lydian.apps.traffic_controller import TrafficControllerApp
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
        'attempts': 2,
        'connected': True
    }

    def setUp(self):
        setup_logging()

        self._delete_db_files()

        # Traffic Records.
        self.traffic_records = getattr(self, 'traffic_records',
                                       queue.Queue(self.MAX_QUEUE_SIZE))
        # Resource records.
        self.resource_records = getattr(self, 'resource_records',
                                        queue.Queue(self.MAX_QUEUE_SIZE))

        self.rulesApp = RulesApp(db_file=self.DB_FILE)
        traffic_tools = getattr(self, 'traffic_tools', {})
        self.controller = TrafficControllerApp(self.traffic_records,
                                               self.rulesApp,
                                               traffic_tools)
        self.monitor = ResourceMonitor(self.resource_records)
        self.results = Results()

        self.db_pool = RecordManager(self.traffic_records, self.resource_records)
        # self.db_pool.start()
        self.monitor.start()

    def _delete_db_files(self, del_config=False):
        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)
        if os.path.exists('./traffic.db'):
            os.remove("./traffic.db")
        if del_config and os.path.exists('./traffic.db'):
            os.remove("./traffic.db")

    def _test_register_traffic(self):
        rules = [('TCP', 9465), ('UDP', 9465), ('HTTP', 9466)]
        traffic_rules = []
        for protocol, port in rules:
            _rule = dict(self.DUMMY_RULE)
            # _rule['reqid'] =  '%s' % uuid.uuid4()
            _rule['ruleid'] = '%s' % uuid.uuid4()
            _rule['protocol'] = protocol
            _rule['port'] = port
            traffic_rules.append(_rule)

        self.reqid = self.DUMMY_RULE['reqid']
        self.controller.register_traffic(traffic_rules)
        time.sleep(10)  # Run traffic for 10 seconds.
        self.traffic_rules = traffic_rules

    def _test_wf_client(self):
        """ Tests WF Clients """
        trec = WavefrontTrafficRecorder()
        t_rec = self.traffic_records.get()
        trec.write(t_rec)

        rrec = WavefrontResourceRecorder()
        r_rec = self.resource_records.get()
        rrec.write(r_rec)

    def _test_recorder(self):
        """ Tests Data Rcorder """
        self.db_pool.start()
        time.sleep(6)   # Wait for 6 seconds for DB Pool to empty queue
        records = self.results.traffic(self.reqid)
        assert records, "Traffic results missing"

    def _test_start_stop_traffic(self):
        # Check for Start / Stop Traffic
        ruleid = self.traffic_rules[0]['ruleid']
        self.controller.stop(ruleid)
        time.sleep(10)  # Stop traffic for 10 seconds
        # Ensure no traffic recorder in last 10 seconds.
        ts = int(time.time())
        records = self.results.traffic(reqid=self.reqid,
                                       ruleid=ruleid,
                                       timestamp=(ts-8, ts))
        assert not pickle.loads(records), "Stop traffic not working..."
        self.controller.start(ruleid)
        time.sleep(10)  # Stop traffic for 10 seconds
        ts = int(time.time())
        records = self.results.traffic(reqid=self.reqid,
                                       ruleid=ruleid,
                                       timestamp=(ts-8, ts))
        assert pickle.loads(records), "Start traffic not working..."

    def _test_persistence(self):
        self.controller.close()
        self.db_pool.close()
        time.sleep(45)
        os.remove('./traffic.db')
        traffic_tools = getattr(self, 'traffic_tools', {})
        self.controller = TrafficControllerApp(self.traffic_records, self.rulesApp,
                                               traffic_tools)
        self.db_pool = RecordManager(self.traffic_records, self.resource_records)
        self.db_pool.start()
        ts = int(time.time())
        time.sleep(10)
        ruleid = self.traffic_rules[0]['ruleid']
        records = self.results.traffic(reqid=self.reqid)
        assert records, "Persistence not working"

    def test_main(self):
        self._test_register_traffic()
        self._test_wf_client()
        self._test_recorder()
        self._test_start_stop_traffic()
        # self._test_persistence()

    def tearDown(self):
        log.info("Stopping Resource Monitor")
        self.monitor.stop()

        log.info("Stopping Rules")
        self.rulesApp.close()

        # Stop Traffic Recorder before Traffic Controller as
        # otherwise recorder threads might be blocked on waiting
        # for data to come in queue.
        log.info("Stopping Recorder")
        self.db_pool.close()

        log.info("Stopping controller")
        self.controller.close()



        log.info("Deleting DB files")
        self._delete_db_files(del_config=True)
