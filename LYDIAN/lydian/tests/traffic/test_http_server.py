#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import threading
import time
import unittest

from lydian.traffic import server as hserver

log = logging.getLogger(__name__)


class HTTPServerTest(unittest.TestCase):
    PORT = 3456
    SERVER_RUN_TIME = 2

    def setUp(self):
        self.server = hserver.HTTPServer(port=self.PORT)

    def _test_one(self):
        self.server.start(blocking=False)
        time.sleep(self.SERVER_RUN_TIME)
        self.server.stop()

    def _test_two(self):
        t = threading.Thread(target=self.server.start,
                             args=(False,), daemon=True)
        t.start()
        time.sleep(self.SERVER_RUN_TIME)
        self.server.stop()

    def _test_three(self):
        t = threading.Thread(target=self.server.start,
                             args=(False,))
        t.start()
        time.sleep(self.SERVER_RUN_TIME)
        self.server.stop()
        t.join()

    def test_usage(self):
        self._test_one()
        self._test_two()
        self._test_three()