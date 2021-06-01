#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import unittest
import uuid

from lydian.traffic.core import TrafficRule, VMHost
from lydian.traffic.manager import ClientManager, ServerManager


log = logging.getLogger(__name__)


class TrafficManagerTest(unittest.TestCase):

    def test_traffic_manager(self):
        """ """
        clientMgr = ClientManager()
        serverMgr = ServerManager()

        rule = TrafficRule()    # Dummy Rule

        rule.ruleid = '%s' % uuid.uuid4()
        rule.src = '127.0.0.1'
        rule.dst = '127.0.0.1'
        rule.port = '3655'
        rule.protocol = 'TCP'

        vm_host = VMHost(name='this_host', ip='127.0.0.1')
        rule.src_host = vm_host
        rule.dst_host = vm_host

        # TEST 1
        # Targets must be specified on Traffic Rule for Traffic Manager
        # to be able to create Client/Servers.
        with self.assertRaises(AttributeError) as err:
            clientMgr.add_task(rule)
            self.assertIn(err.args, "has no attribute 'src_target'")

        # TEST 2:
        # Fix targets and host
        rule.src_host = '127.0.0.1'
        rule.dst_host = '127.0.0.1'
        rule.src_target = vm_host
        rule.dst_target = vm_host

        serverMgr.add_task(rule)
        clientMgr.add_task(rule)

        # TEST 3:
        # Adding another server for same rule shouldn't cause error.
        serverMgr.add_task(rule)
        clientMgr.add_task(rule)
        self.assertEqual(clientMgr.num_tasks(), 1)
        self.assertEqual(serverMgr.num_tasks(), 1)

        # TEST 4:
        # Pretend to be different rule with same configuration.
        rule.ruleid = '%s' % uuid.uuid4()   # pretend to be a different rule.

        # Adding another server for different rule won't cause error and
        # number of active tasks still should be one.
        serverMgr.add_task(rule)
        # Creating a new client for same config but different rule is OK.
        clientMgr.add_task(rule)
        self.assertEqual(clientMgr.num_tasks(), 2)  # 2 clients now.
        self.assertEqual(serverMgr.num_tasks(), 1)  # but only 1 server.
