#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
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

import psutil

from jasper.apps.base import BaseApp, exposify
from jasper.recorder.record import ResourceRecord

log = logging.getLogger(__name__)


@exposify
class ResourceMonitor(BaseApp):
    def __init__(self, rqueue, interval=3, proc_name='runner'):
        """
        A simple resource monitor that writes cpu / memory percentage
        to wavefront at requested interval.
        """
        self._rqueue = rqueue    # records queue to put records onto.
        self._interval = interval
        self._switch = threading.Event()
        self._proc_name = proc_name
        self._thread = None

    def _run(self):
        p = psutil.Process(os.getpid())
        while self._switch.is_set():
            sys_cpu_percent = round(psutil.cpu_percent(), 2)
            sys_mem_percent = round(psutil.virtual_memory().percent, 2)
            sys_net_conns = int(len(psutil.net_connections()))

            jasper_cpu_percent = round(p.cpu_percent(), 2)
            jasper_mem_percent = round(p.memory_percent(), 2)
            jasper_net_conns = int(len(p.connections()))

            rec = ResourceRecord(sys_cpu_percent, sys_mem_percent,
                                 sys_net_conns,
                                 jasper_cpu_percent, jasper_mem_percent,
                                 jasper_net_conns)
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
        self._switch.clear()
        if self.is_running():
            self._thread.join()
            self._thread = None
        log.info("Stopped resource monitoring.")

    def start(self):
        """
        Starts Resource monitoring (in a separate thread)
        """
        self._switch.set()
        if not self._thread:
            self._thread = threading.Thread(target=self._run)
            self._thread.setDaemon(True)
            self._thread.start()
        log.info("Started resource monitoring.")