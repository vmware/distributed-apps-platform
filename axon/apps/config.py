#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
from sql30 import db


from axon.apps.base import BaseApp

log = logging.getLogger(__name__)
configs = None


class Config(db.Model, BaseApp):
    NAME = "CONFIG"
    DB_NAME = 'config.db'
    TABLE = 'config'
    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': {
                    'param': 'text',
                    'value': 'text',
                    },
            }]
        }
    VALIDATE_BEFORE_WRITE = True

<<<<<<< HEAD
    def __init__(self):
        super(Config, self).__init__()
=======
    DEFAULT_CONFIG = '/etc/axon/axon.conf'

    def __init__(self, db_file=None):
        # Set database name.
        db_name = db_file or self.DB_NAME
        super(Config, self).__init__(db_name=db_name)
        self.table = self.TABLE

        # set params
>>>>>>> 9e6d7e7... axon: Unit test for config app
        self._params = {}

        # Read configs, load from db file.
        self._read_config()
        self._update_from_db()
        self.save_params()

    def _read_config(self):
        configs = []
<<<<<<< HEAD
        with open('/etc/axon/axon.conf', 'r') as fp:
            configs = fp.readlines()
=======
        if os.path.exists(self.DEFAULT_CONFIG):
            with open(self.DEFAULT_CONFIG, 'r') as fp:
                configs = fp.readlines()
>>>>>>> 9e6d7e7... axon: Unit test for config app

        for config in configs:
            config = config.strip()
            if config.startswith('#'):
                continue
            param, val = config.split('=')
            self.set_param(param, val,
                           write_to_db=False)

    def _update_from_db(self):
        """
        Local database / persisted file is the source of truth.
        It will override the values read from config file.
        """
<<<<<<< HEAD
        pass
=======
        configs = self.read()
        for key, val in configs:
            self._params[key] = val

    def save_to_db(self):
        """
        Save config params in local cache to database file.
        """
        for param, val in self._params.items():
            self._persist_param(param, val)

        self.commit()
>>>>>>> 9e6d7e7... axon: Unit test for config app

    def get_param(self, param):
        if param in self._params:
            # local params would always be updated.
            return self._params[param]

        records = self.read(self.TABLE, param=param)
        # TODO : avoid multiple records by using primary key
        if records:
            return records[0][1]
        return None

    def set_param(self, param, val, write_to_db=True):
        self._params[param] = val
        if write_to_db:
            self.write(self.TABLE, param=param, value=val)

<<<<<<< HEAD
    def save_params(self):
        for key, val in self._params.items():
            self.write(self.TABLE, param=key, value=val)
        self.commit()
=======
    def _persist_param(self, param, val):
        """
        Sets a param, val in database file.
        """
        record = self.read(param=param)
        if record:
            self.update(condition={'param':param}, value=val)
        else:
            self.write(param=param, value=val)
>>>>>>> 9e6d7e7... axon: Unit test for config app


def _get_configs():
    global configs
    if not configs:
        configs = Config()

    return configs


def get_param(param):
    return _get_configs().get_param(param)


def set_param(param, val):
    return _get_configs().set_param(param, val)
