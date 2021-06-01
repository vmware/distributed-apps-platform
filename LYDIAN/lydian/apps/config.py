#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import json
import logging
import os
import platform
import socket
import sys
from collections import defaultdict

from sql30 import db

import lydian.apps.base as base
import lydian.common.consts as consts 


log = logging.getLogger(__name__)
configs = None


class ConfigDB(db.Model):
    DB_NAME = './params.db'
    TABLE = 'config'

    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': {
                    'param': 'text',
                    'value': 'text',
                    'typename': 'text',
                    },
                'primary_key': 'param'  # avoid duplicate entries.
            }]
        }
    VALIDATE_BEFORE_WRITE = True


class Config(ConfigDB, base.BaseApp):
    BOOLS = ('TRUE', 'FALSE')
    NAME = "CONFIG"

    def __init__(self, db_file=None):
        # Set database name.
        db_name = db_file or self.DB_NAME
        super(Config, self).__init__(db_name=db_name)
        self.table = self.TABLE

        # set params
        self._params = {}

        # subscribers to notify upon value update
        self._subscribers = defaultdict(set)

        # Initialize params as default.
        self._set_defaults()

        # Override user provided configs.
        self._read_config()

        # Load any dynamically modified configs.
        self.load_from_db()

        # Save latest configs to DB
        self.save_to_db()

    def _read_config(self):
        """
        Reads config from default config file.

        We do not write these configs into the database yet as database
        configs are supposed to overwrite.
        """
        try:
            cfg_file = self.get_param('LYDIAN_CONFIG')
            with open(cfg_file, 'r') as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith('#'):
                        continue
                    else:
                        try:
                            # handle cases like 'x="deployment=ovf"'
                            kindex = line.index('=')
                            param = line[:kindex].strip()
                            val = line[kindex+1:].strip()
                            val = val.strip('"')
                            val = val.strip("'")
                            if val.upper() in self.BOOLS:
                                val = True if val.upper() == "TRUE" else False
                            else:
                                try:
                                    _ = float(val)
                                    val = int(_) if round(_) == _ else _
                                except ValueError:
                                    pass
                            self._params[param] = val
                        except ValueError:
                            pass
        except FileNotFoundError:
            pass

    def _set_defaults(self):
        """
        Initialized params with default constants.
        """
        for param, val in consts.get_constants().items():
            if str(val).upper() in self.BOOLS:
                val = True if str(val).upper() == "TRUE" else False
            self._params[param] = val

    def _type_handler(self, val, type_name):

        types_map = {
                'int': lambda x: int(x),
                'float': lambda x: float(x),
                'tuple': lambda x: tuple(x),
                'set': lambda x: set(x),
                'bool': lambda x: True if x == True else False,
                'NoneType': lambda x: None,
            }
        val = json.loads(val)

        return types_map[type_name](val) if type_name in types_map else val

    def load_from_db(self):
        """
        Load config params from database file to local cache.
        """
        configs = []
        with ConfigDB() as db:
            configs = db.read(tbl=self.TABLE)
        for key, val, type_name in configs:
            self._params[key] = self._type_handler(val, type_name)

    def save_to_db(self):
        """
        Save config params in local cache to database file.
        """
        with ConfigDB() as db:
            db.table = self.TABLE
            for param, val in self._params.items():
                self._persist_param(param, val, db)

    def get_param(self, param, default=None):
        """
        Return the value of a config param. Param is always
        returned from local cache as it is simply a reflector of database file.
        """
        return self._params.get(param, default)

    def set_param(self, param, val, write_to_db=True):
        self._params[param] = val

        if write_to_db:
            with ConfigDB() as db:
                db.table = self.TABLE
                self._persist_param(param, val, db)
                self._notify_subscriber(param)

    def subscribe_notification(self, params, subscriber, callback):
        for param in params:
            if param in self._params and callable(getattr(subscriber, callback, None)):
                self._subscribers[param].add((subscriber, callback))
            else:
                log.warn('Skip subscribing: %s since it is not in supported config params', param)

    def unsubscribe_notification(self, params, subscriber, callback):
        for param in params:
            if param in self._subscribers:
                self._subscribers[param].discard((subscriber, callback))

    def _notify_subscriber(self, param):
        if param in self._subscribers:
            for subscriber, callback in self._subscribers[param]:
                _callback = getattr(subscriber, callback)
                _callback(param)

    def _persist_param(self, param, val, db_handle):
        """
        Sets a param, val in database file.
        """
        type_name = type(val).__name__
        if isinstance(val, set):
            # json.dumps can't serialize sets. We still return the
            # value as set as type is stored as "set"
            val = list(val)
        record = db_handle.read(param=param)
        if record:
            db_handle.update(condition={'param': param},
                             value=json.dumps(val),
                             typename=type_name)
        else:
            db_handle.write(param=param,
                            value=json.dumps(val),
                            typename=type_name)

    exposed_get_param = get_param
    exposed_set_param = set_param

    def write_config_file(self, file_name, overwrite=True):
        mode = 'w+' if overwrite  else 'w'
        marker = '#' * 5
        with open(file_name, mode) as fp:
            fp.write("### LYDIAN Service Config file ###")
            for category in consts.get_categories():
                fp.write("\n\n")
                fp.write("%s %s constants %s" % (marker,
                    category._NAME, marker))
                for key, val in consts.get_constants([category]).items():
                    if isinstance(val, str):
                        fp.write("\n%s = '%s'" % (key, self.get_param(key)))
                    elif isinstance(val, bool):
                        val = 'True' if self.get_param(key) else 'False'
                        fp.write("\n%s = '%s'" % (key, val))
                    else:
                        fp.write('\n%s = %s' % (key, self.get_param(key)))

            fp.write("\n\n### LYDIAN Service Config (END) ###\n")

    def cleanup(self):
        """
        Remove local DB file.
        """
        if os.path.exists(self._db):
            os.remove(self._db)


def get_configs():
    global configs
    if not configs:
        configs = Config()

    return configs


def get_param(param, default=None):
    return get_configs().get_param(param, default)


def set_param(param, val):
    return get_configs().set_param(param, val)


def update_config():
    """ Update Config file at local installation """
    data_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(data_dir, '../data')
    cfg_file = os.path.join(data_dir, 'lydian.conf')
    get_configs().write_config_file(file_name=cfg_file)