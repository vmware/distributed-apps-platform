#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
import sqlite3
import unittest
import uuid

from lydian.apps.rules import RulesApp


DB_NAME = 'rules_test.db'
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
        class DummyTrafficManager(object):

            def start(self, ruleid):
                log.info("Starting Traffic for rule %s ", ruleid)

            def stop(self, ruleid):
                pass

        return RulesApp(DummyTrafficManager(), DB_NAME)

    def test_add(self):
        self.rulesApp = self._get_new_app()

        # TEST : Add one rule
        self.rulesApp.add(self.DUMMY_RULE)

        # TEST : Adding same rule would lead to a warning
        # but no assertion / exception to break the run.
        self.rulesApp.add(self.DUMMY_RULE)

        rules = []
        for x in range(5):
            rule = {k: v for k, v in self.DUMMY_RULE.items()}
            rule['ruleid'] = '%s' % uuid.uuid4()
            rules.append(rule)

        # TEST : Adding multiple rules.
        self.rulesApp.add_rules(rules)

        self.rulesApp.save_to_db()
        self.rulesApp.close()

        # Get New instance of rulesApp()
        # If persistence works, all the rules must be brought up fine.
        self.rulesApp = self._get_new_app()

        self.rulesApp.load_from_db()

        # TEST : All the rules must be prsent.
        rules.append(self.DUMMY_RULE)

        for rule in rules:
            assert self.rulesApp.get(rule['ruleid'])

        # TEST : Diable / Enable of rules should work.
        self.rulesApp.disable(rules[0]['ruleid'])
        # disable and enable the rule
        self.rulesApp.disable(rules[1]['ruleid'])
        self.rulesApp.enable(rules[1]['ruleid'])

        assert not self.rulesApp.is_enabled(rules[0]['ruleid'])
        assert self.rulesApp.is_enabled(rules[1]['ruleid'])

    def tearDown(self):
        os.remove(DB_NAME)
