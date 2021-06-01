#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
import sqlite3
import unittest
import uuid

from lydian.apps.rules import RulesApp
from lydian.traffic.core import TrafficRule


DB_NAME = './rules_test.db'
log = logging.getLogger(__name__)


class RulesAppTest(unittest.TestCase):

    DUMMY_RULE = {
        'ruleid': '%s' % uuid.uuid4(),
        'src': '127.0.0.1',
        'dst': '127.0.0.1',
        'protocol': 'TCP',
        'port': 9465,
        'connected': False
    }

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def _get_new_app(self):
        return RulesApp(DB_NAME)

    def _get_trule(self, rule):
        trule = TrafficRule()
        for k, v in rule.items():
            setattr(trule, k, v)
        trule.fill()
        return trule

    def test_add(self):
        self.rulesApp = self._get_new_app()
        trule = self._get_trule(self.DUMMY_RULE)

        self.rulesApp.add(trule)

        # TEST : Add one rule
        self.rulesApp.add(trule)

        # TEST : Adding same rule would lead to a warning
        # but no assertion / exception to break the run.
        self.rulesApp.add(trule)

        trules = []
        for x in range(5000):
            rule = {k: v for k, v in self.DUMMY_RULE.items()}

            rule['ruleid'] = '%s' % uuid.uuid4()
            trule = self._get_trule(rule)
            trules.append(trule)

        # TEST : Adding multiple rules.
        self.rulesApp.add_rules(trules)

        self.rulesApp.close()

        # Get New instance of rulesApp()
        # If persistence works, all the rules must be brought up fine.
        self.rulesApp = self._get_new_app()

        self.rulesApp.load_from_db()

        # TEST : All the rules must be prsent.

        assert self.rulesApp.get(trule.ruleid)
        for trule in trules:
            assert self.rulesApp.get(trule.ruleid)

        # TEST : Diable / Enable of rules should work.
        self.rulesApp.disable(trules[0].ruleid)
        # disable and enable the rule
        self.rulesApp.disable(trules[1].ruleid)
        self.rulesApp.enable(trules[1].ruleid)

        assert not self.rulesApp.is_enabled(trules[0].ruleid)
        assert self.rulesApp.is_enabled(trules[1].ruleid)

    def tearDown(self):
        os.remove(DB_NAME)
