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


from lydian.apps.config import get_configs
from lydian.apps.interface import InterfaceApp
from lydian.apps.iperf import Iperf
from lydian.apps.monitor import ResourceMonitor
from lydian.apps.namespace import NamespaceApp
from lydian.apps.tcpdump import TCPDump
from lydian.apps.controller import TrafficControllerApp
from lydian.apps.recorder import RecordManager
from lydian.apps.results import Results
from lydian.apps.rules import RulesApp

import lydian.utils.logger as logger
import lydian.apps.config as config
import lydian.common.consts as consts

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

    EXPOSED = [
        'monitor',
        'namespace',
        'rules',
        'interface',
        'iperf',
        'tcpdump',
        'results',
        'controller'
    ]

    def __init__(self):
        super(LydianService, self).__init__()

        self._traffic_records = Queue(self.RECORD_QUEUE_SIZE)
        self._resource_records = Queue(self.RECORD_QUEUE_SIZE)

        self.recorder = RecordManager(self._traffic_records,
                                      self._resource_records)

        self.namespace = NamespaceApp()
        self.interface = InterfaceApp()
        self.rules = RulesApp()
        self.controller = TrafficControllerApp(self._traffic_records,
                                               self.rules)
        self.monitor = ResourceMonitor(self._resource_records)
        self.tcpdump = TCPDump()
        self.iperf = Iperf()
        self.results = Results()

        self.expose()

    def expose(self):
        for key in self.EXPOSED:
            setattr(self, 'exposed_'+ key, getattr(self, key))

    def start(self):
        try:
            self.monitor.start()
            self.recorder.start()
        except Exception as err:
            self.logger.exception("Error in starting Services %r", err)

    def stop(self):
        try:
            self.monitor.stop()
            self.recorder.stop()
        except Exception as err:
            self.logger.exception("Error while stopping Services %r", err)


class LydianController(object):

    def __init__(self):
        self.lydian_port = consts.LYDIAN_PORT
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
        self.service.start()
        self.lydian_service.start()

    def stop(self):
        self.service.stop()
        self.lydian_service.close()


def main():
    logger.setup_logging(log_dir=config.LOG_DIR,
                         log_file=config.LOG_FILE)
    lydian_service = LydianController()
    lydian_service.start()


if __name__ == '__main__':
    main()
