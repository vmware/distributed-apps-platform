#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
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

<<<<<<< HEAD
<<<<<<< HEAD:jasper/apps/config.py
<<<<<<< HEAD
from axon.apps.base import BaseApp
from axon.common import consts, utils
=======
from jasper.apps.base import BaseApp
<<<<<<< HEAD
import jasper.utils.logger as logger
>>>>>>> f88c338... lydian: RPyC srvice
=======
=======
from lydian.apps.base import BaseApp
>>>>>>> d9f9229... lydian : Initial changes to prepare for release - lydian 0.1.0:lydian/apps/config.py
=======
import lydian.apps.base as base
import lydian.common.consts as consts 
>>>>>>> e11d80d... lydian: Integrate node preparation with constants, configs updates.

>>>>>>> 17eec04... Lydian: Remove cyclic dependency

log = logging.getLogger(__name__)
configs = None

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
#### CONSTANTS ####
=======
# CONSTANTS
>>>>>>> ef09167... lydian: Fix ValueError in config
SYSTEM = platform.system()
LINUX_OS = True if SYSTEM == 'Linux' else False
MAC_OS = True if SYSTEM == 'Darwin' else False
WIN_OS = True if SYSTEM == 'Windows' else False

# Logging Constants
LINUX_LOG_DIR = os.environ.get('LINUX_LOG_DIR', "/var/log/lydian")
WIN_LOG_DIR = os.environ.get('WIN_LOG_DIR', "C:\\lydian\\log")
if LINUX_OS or MAC_OS:
    LOG_DIR = LINUX_LOG_DIR
elif WIN_OS:
    LOG_DIR = WIN_LOG_DIR
LOG_FILE = "lydian.log"

# Lydian Service Constants
LYDIAN_PORT = 5649

# Recorder Constants
WAVEFRONT = 'wavefront'
SQL = 'sql'
ELASTIC_SEARCH = 'elasticsearch'
ELASTIC_SEARCH_PORT = 9200
>>>>>>> f88c338... lydian: RPyC srvice

# # # # # All Configurable Variables set below # # # # #

<<<<<<< HEAD
LINUX_OS = "Linux" in platform.uname()
LOG_FILE = os.environ.get('LOG_FILE', consts.LOG_FILE)
LOG_DIR = os.environ.get('LOG_DIR', consts.LOG_DIR)
utils.setup_logging(log_dir=LOG_DIR, log_file=LOG_FILE)

=======
>>>>>>> 17eec04... Lydian: Remove cyclic dependency

# Traffic Server Configs
REQUEST_QUEUE_SIZE = 100
PACKET_SIZE = 1024
ALLOW_REUSE_ADDRESS = True


# Env Configs
TEST_ID = os.environ.get('TEST_ID', '1234')
TESTBED_NAME = os.environ.get('TESTBED_NAME', 'LYDIAN_DFLT_TB')
LYDIAN_PORT = int(os.environ.get('LYDIAN_PORT', LYDIAN_PORT))
LYDIAN_CONFIG = os.environ.get('LYDIAN_CONFIG', '/etc/lydian/lydian.conf')

# Wavefront recorder configs
WAVEFRONT_TRAFFIC_RECORDING = os.environ.get('WAVEFRONT_TRAFFIC_RECORDING',
                                             True)
WAVEFRONT_RESOURCE_RECORDING = os.environ.get('WAVEFRONT_RESOURCE_RECORDING',
                                              True)
WAVEFRONT_PROXY_ADDRESS = os.environ.get('WAVEFRONT_PROXY_ADDRESS', None)
WAVEFRONT_PROXY_METRICS_PORT = os.environ.get('WAVEFRONT_PROXY_METRICS_PORT', 2878)
WAVEFRONT_PROXY_DISTRIBUTION_PORT = os.environ.get('WAVEFRONT_PROXY_DISTRIBUTION_PORT', 2878)
WAVEFRONT_PROXY_TRACING_PORT = os.environ.get('WAVEFRONT_PROXY_TRACING_PORT', 30000)
WAVEFRONT_PROXY_EVENT_PORT = os.environ.get('WAVEFRONT_PROXY_EVENT_PORT', 2878)

WAVEFRONT_SERVER_ADDRESS = os.environ.get('WAVEFRONT_SERVER_ADDRESS',
                                          'https://vmware.wavefront.com')
WAVEFRONT_SERVER_API_TOKEN = os.environ.get('WAVEFRONT_SERVER_API_TOKEN', '')

WAVEFRONT_SOURCE_TAG = os.environ.get('WAVEFRONT_SOURCE', socket.gethostname())
WAVEFRONT_REPORT_PERC = float(os.environ.get('WAVEFRONT_REPORT_PERC', 1.0))



# SQLITE recording configs
SQLITE_TRAFFIC_RECORDING = os.environ.get('SQLITE_TRAFFIC_RECORDING', True)
SQLITE_RESOURCE_RECORDING = os.environ.get('SQLITE_RESOURCE_RECORDING', True)
# Namespace Configs
NAMESPACE_MODE = os.environ.get("NAMESPACE_MODE", False)
NAMESPACE_MODE = True if NAMESPACE_MODE in ['True', True] else False
NAMESPACE_INTERFACE_NAME_PREFIXES = ["veth", "eth"]


# Recorder Configs
RECORDER = os.environ.get('RECORDER', None)
RECORD_UPDATER_THREAD_POOL_SIZE = int(os.environ.get('RECORD_UPDATER_THREAD_POOL_SIZE', 2))
RESOURCE_RECORD_REPORT_FREQ = int(os.environ.get('RESOURCE_RECORD_REPORT_FREQ', 4))
TRAFFIC_RECORD_REPORT_FREQ = int(os.environ.get('TRAFFIC_RECORD_REPORT_FREQ', 4))
RECORD_COUNT_UPDATER_SLEEP_INTERVAL = int(os.environ.get('RECORD_COUNT_UPDATER_SLEEP_INTERVAL', 30))
RECORD_UPDATER_THREAD_POOL_SIZE = int(os.environ.get('RECORD_UPDATER_THREAD_POOL_SIZE', 50))

ELASTIC_SEARCH_SERVER_ADDRESS = os.environ.get('ELASTIC_SEARCH_SERVER_ADDRESS',
                                               None)
ELASTIC_SEARCH_SERVER_PORT = os.environ.get(
    'ELASTIC_SEARCH_SERVER_PORT', ELASTIC_SEARCH_PORT)

# # # # # End of Configurable Variables  # # # # #

=======
>>>>>>> e11d80d... lydian: Integrate node preparation with constants, configs updates.

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

    def get_param(self, param):
        """
        Return the value of a config param. Param is always
        returned from local cache as it is simply a reflector of database file.
        """
        return self._params.get(param, None)

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
            if param in self._subscriber:
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


def get_configs():
    global configs
    if not configs:
        configs = Config()

    return configs


def get_param(param):
    return get_configs().get_param(param)


def set_param(param, val):
    return get_configs().set_param(param, val)


def update_config():
    """ Update Config file at local installation """
    data_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(data_dir, '../data')
    cfg_file = os.path.join(data_dir, 'lydian.conf')
    get_configs().write_config_file(file_name=cfg_file)