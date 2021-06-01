#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
-App for Resource Monitoring.
-Collects System CPU/Memory as well as AXON CPU/ Memory.
"""
import logging
import os
import queue
import threading
import time

import lydian.common.errors as errors

try:
    import psutil
except errors.ModuleNotFoundError:
    import lydian.utils.lpsutil as psutil

from lydian.apps.base import BaseApp, exposify
from lydian.recorder.record import ResourceRecord

log = logging.getLogger(__name__)


@exposify
class ResourceMonitor(BaseApp):

    REPORT_INTERVAL = 2
    def __init__(self, rqueue, interval=None, proc_name='runner'):
        """
        A simple resource monitor that writes cpu / memory percentage
        to wavefront at requested interval.
        """
        self._rqueue = rqueue    # records queue to put records onto.
        self._interval = interval or self.REPORT_INTERVAL
        self._stop_switch = threading.Event()
        self._stop_switch.set()  # Stopped until started.
        self._proc_name = proc_name
        self._thread = None

    def stopped(self):
        return self._stop_switch.is_set()

    def _run(self):
        p = psutil.Process(os.getpid())
        while not self._stop_switch.is_set():
            sys_cpu_percent = round(psutil.cpu_percent(), 2)
            sys_mem_percent = round(psutil.virtual_memory().percent, 2)
            sys_net_conns = int(len(psutil.net_connections()))

            lydian_cpu_percent = round(p.cpu_percent(), 2)
            lydian_mem_percent = round(p.memory_percent(), 2)
            lydian_net_conns = int(len(p.connections()))

            rec = ResourceRecord(sys_cpu_percent, sys_mem_percent,
                                 sys_net_conns,
                                 lydian_cpu_percent, lydian_mem_percent,
                                 lydian_net_conns)
            try:
                self._rqueue.put(rec, block=False, timeout=2)
            except queue.Full:
                log.error("Cann't put Resource record %r into the queue.",
                          rec)

            time.sleep(self._interval)

    def is_running(self):
        """
        Returns True if Rescoures are being monitored else False.
        """
        return self._thread and self._thread.is_alive()

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
            self._thread = threading.Thread(target=self._run)
            self._thread.setDaemon(True)
            self._thread.start()
        log.info("Started resource monitoring.")
