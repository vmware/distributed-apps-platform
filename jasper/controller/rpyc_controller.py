#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import collections
import logging
# from multiprocessing import Queue
from queue import Queue

import rpyc
from rpyc.utils.server import ThreadPoolServer

from jasper.apps import config as conf

from jasper.apps.config import get_configs
from jasper.apps.interface import InterfaceApp
from jasper.apps.iperf import Iperf
from jasper.apps.monitor import ResourceMonitor
from jasper.apps.namespace import NamespaceApp
from jasper.apps.tcpdump import TCPDump
from jasper.apps.controller import TrafficControllerApp
from jasper.apps.recorder import RecordManager
from jasper.apps.results import Results
from jasper.apps.rules import RulesApp

rpyc.core.protocol.DEFAULT_CONFIG['allow_pickle'] = True


class LydianServiceBase(rpyc.Service):

    RPYC_PROTOCOL_CONFIG = rpyc.core.protocol.DEFAULT_CONFIG

    def __init__(self):
        super(LydianServiceBase, self).__init__()

    def on_connect(self, conn):
        print("Connected to %r", conn)

    def on_disconnect(self, conn):
        print("Disconnected from %r", conn)


class LydianService(LydianServiceBase):
    RECORD_QUEUE_SIZE = 50000

    def __init__(self):
        super(LydianService, self).__init__()

        self._traffic_records = Queue(self.RECORD_QUEUE_SIZE)
        self._resource_records = Queue(self.RECORD_QUEUE_SIZE)

        self.namespace = NamespaceApp()
        self.interface = InterfaceApp()
        self.rules = RulesApp()
        self.traffic = TrafficControllerApp(self._traffic_records, self.rules)
        self.monitor = ResourceMonitor(self._resource_records)
        self.tcpdump = TCPDump()
        self.iperf = Iperf()
        self.results = Results()
        self.recorder = RecordManager(self._traffic_records, self._resource_records)


class LydianController(object):

    def __init__(self):
        self.lydian_port = conf.AXON_PORT
        self.service = LydianService()
        self.protocol_config = self.service.RPYC_PROTOCOL_CONFIG
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARN)
        self.lydian_service = ThreadPoolServer(
            self.service,
            port=self.lydian_port,
            reuse_addr=True,
            protocol_config=self.protocol_config,
            logger=self.logger, nbThreads=50)

    def start(self):
        try:
            self.service.monitor.start()
        except Exception as err:
            self.logger.exception("Error in starting Resource Monitoring - "
                                  "%r", err)
        self.lydian_service.start()

    def stop(self):
        try:
            self.service.monitor.stop()
        except Exception as err:
            self.logger.exception("Error while stopping Resource Monitoring - "
                                  "%r", err)

        self.lydian_service.close()


def main():
    lydian_service = LydianController()
    lydian_service.start()


if __name__ == '__main__':
    main()
