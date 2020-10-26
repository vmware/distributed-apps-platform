#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
Unit test for Console app.
'''
import logging
import unittest

from axon.apps.console import Console


log = logging.getLogger(__name__)


class TestConsoleApp(unittest.TestCase):

    def setUp(self):
        super(TestConsoleApp, self).setUp()
        self._console = Console()

    def test_ls_command(self):
        # Simple command
        status, result = self._console.run_command("ls -lrt")
        log.info("Status: %s, Result:%s" % (status, result))

    def test_ping_fail_command(self):
        # Simple command
        # Timeout failure
        status, result = self._console.run_command("ping 127.0.0.1",
                                                   timeout=1)
        log.info("Status: %s, Result:%s" % (status, result))
