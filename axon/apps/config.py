#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
from sql30 import db


from axon.apps.base import BaseApp

log = logging.getLogger(__name__)
configs = None


class Config(db.Model, BaseApp):
    NAME = "CONFIG"

    TABLE = 'config'
    DB_SCHEMA = {
        'db_name': 'config.db',
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

    def __init__(self):
        super(Config, self).__init__()
        self._params = {}
        self._read_config()
        self._update_from_db()
        self.save_params()

    def _read_config(self):
        configs = []
        with open('/etc/axon/axon.conf', 'r') as fp:
            configs = fp.readlines()

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
        pass

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

    def save_params(self):
        for key, val in self._params.items():
            self.write(self.TABLE, param=key, value=val)
        self.commit()


def _get_configs():
    global configs
    if not configs:
        configs = Config()

    return configs


def get_param(param):
    return _get_configs().get_param(param)


def set_param(param, val):
    return _get_configs().set_param(param, val)
