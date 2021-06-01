#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
import queue
import threading
import time


from lydian.apps.base import BaseApp, exposify
from lydian.traffic.core import TrafficRecord, TrafficRule
from lydian.utils.common import get_mgmt_ifname
from lydian.utils.network_utils import InterfaceManager

log = logging.getLogger(__name__)


@exposify
class MockTraffic(BaseApp):

    REPORT_INTERVAL = 5
    def __init__(self, rqueue, interval=None, proc_name='runner'):
        """
        A simple resource monitor that writes cpu / memory percentage
        to wavefront at requested interval.
        """
        self._rqueue = rqueue    # records queue to put records onto.
        self._interval = interval or self.REPORT_INTERVAL
        self._stop_switch = threading.Event()
        self._stop_switch.set()  # Stopped until started.
        self._thread = None
        self._dummy_rule = {}

        # Host is where this app is running. Based on host,
        # it is decided for a rule if we need to run a client
        # or server.
        ifname = get_mgmt_ifname()
        self.host = InterfaceManager().get_interface(ifname)['address']

    @property
    def enabled(self):
        return not self._stop_switch.is_set()

    def register_traffic(self, rules):
        for rule in rules:
            if not isinstance(rule, TrafficRule):
                log.error("Improper rule : %r", rule)
                continue
            if self.host == rule.src_host:
                # For client side just do a bookkeeping.
                self._dummy_rule[rule.ruleid] = rule
            if self.host == rule.dst_host:   # Noop for server
                continue
            log.info("Registered traffic : %r", rule.ruleid)

    def ping(self):
        while not self._stop_switch.is_set():
            # Put logic for running traffic here. 
            # Process the response and create Traffic Record
            # like below and put on the queue. It will be pushed
            # onto corresponding databases.

            for ruleid, trule in self._dummy_rule.items():
                # as an example, create dummy records for each ruleid
                # asked to be handled by this tool.
                try:
                    rec = TrafficRecord()
                    rec.source = '0.0.0.0'
                    rec.destination = '0.0.0.0'
                    rec.protocol = 'TCP'
                    rec.port = '00'
                    rec.result = True
                    rec.reqid = trule.reqid
                    rec.ruleid = ruleid
                    rec.latency = '0'
                    self._rqueue.put(rec, block=False, timeout=2)
                    log.info("Traffic: %r", rec)
                except queue.Full as err:
                    log.error("Cann't put Traffic Record %r into the queue: %r",
                            rec, err)
                except Exception as err:
                    log.error("Error in puytting dummy records %r ",err)

            time.sleep(self._interval)

    def is_running(self):
        """
        Returns True if Rescoures are being monitored else False.
        """
        return self._thread and self._thread.is_alive()

    def start_traffic(self, trule):
        self._dummy_rule[trule.ruleid] = trule
        log.info("Starting traffic for rule : %s", trule.ruleid)

    def stop_traffic(self, trule):
        self._dummy_rule.pop(trule.ruleid)
        log.info("Stopped traffic for rule : %s", trule.ruleid)

    def stop(self):
        """
        Stops Resource Monitoring.
        """
        self._stop_switch.set()
        if self.is_running():
            self._thread.join()
            self._thread = None
        log.info("Stopped resource monitoring.")

    def start(self):
        """
        Starts Resource monitoring (in a separate thread)
        """
        self._stop_switch.clear()
        if not self._thread:
            self._thread = threading.Thread(target=self.ping)
            self._thread.setDaemon(True)
            self._thread.start()
        log.info("Started resource monitoring.")