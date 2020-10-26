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

from axon.apps.config import Config


DB_NAME = 'config_test.db'

log = logging.getLogger(__name__)


class ConfigAppTest(unittest.TestCase):
    DUMMY_DATA = {
        'param1': 'val1',
        'param2': 'val2',
        'param3': 'val3',
        'param4': 1,  # integer test
        'param5': 1.03,  # float test
        'param6': ['val1', 'val2', 'val3'],  # list test
        'param7': ("val1", "val2", "val3"),  # tuple test
        'param8': {"key1": 1, "key2": "value2"},  # dict test
        'param9': False,
        'param10': True,
        }

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def _get_new_app(self):
        return Config(db_file=DB_NAME)

    def test_add(self):
        self.app = self._get_new_app()

        # TEST : Adding params in Config
        for param, val in self.DUMMY_DATA.items():
            self.app.set_param(param=param, val=val)

        # TEST : Adding same values would lead to a warning
        # but no assertion / exception to break the run.
        for param, val in self.DUMMY_DATA.items():
            self.app.set_param(param=param, val=val)

        self.app.save_to_db()
        self.app.close()

        # Get New instance of app()
        # If persistence works, all the rules must be brought up fine.
        self.app = self._get_new_app()

        # TEST : All the params must be present.
        for param, val in self.DUMMY_DATA.items():
            self.assertEqual(val, self.app.get_param(param))
            self.assertEqual(type(val), type(self.app.get_param(param)))

    def tearDown(self):
        os.remove(DB_NAME)
