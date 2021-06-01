#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import queue
import time
import unittest

from lydian.common.background import BackgroundMixin

log = logging.getLogger(__name__)

class BackJob(BackgroundMixin):

    def __init__(self):
        super(BackJob, self).__init__()
        self.recs = queue.Queue(1000)
        self._run = self.run

    def run(self):
        while not self.stopped:
            try:
                self.recs.put(100)
            except queue.Full:
                pass
            finally:
                time.sleep(3)


class BackJobTest(unittest.TestCase):

    def setUp(self):
        self.bjob = BackJob()

    def test_back_job(self):
        self.assertEqual(self.bjob.recs.qsize(), 0)

        self.bjob.on()  # Start processing
        time.sleep(10)

        assert self.bjob.recs.qsize(), "Backgroundjob didn't start"

        self.bjob.off()
        while True:
            try:
                _ = self.bjob.recs.get_nowait()
            except queue.Empty:
                break

        time.sleep(10)
        self.assertEqual(self.bjob.recs.qsize(), 0)