#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import queue
import threading

from axon.apps.base import BaseApp
from jasper.traffic.core import TrafficRecord
from sql30 import db


log = logging.getLogger(__name__)


class TrafficRecordDB(db.Model):
    DB_NAME = 'traffic.db'
    TABLE = 'traffic'

    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': {
                    'timestamp': 'text',
                    'reqid': 'text',
                    'ruleid': 'text',
                    'source': 'text',
                    'destination': 'text',
                    'protocol': 'text',
                    'port': 'text',
                    'expected': 'text',
                    'result': 'text'
                    },
                'primary_key': 'timestamp'  # avoid duplicate entries.
            }]
        }
    VALIDATE_BEFORE_WRITE = True


class TrafficRecorder(TrafficRecordDB, BaseApp):
    NAME = "TRAFFIC_RECORDER"

    MAXSIZE = 3000
    FLUSH_FREQ = 3  # every 3 seconds.

    def __init__(self, db_file=None):
        # Set database name.
        db_name = db_file or self.DB_NAME
        super(TrafficRecorder, self).__init__(db_name=db_name)
        self._fields = self._get_fields(self.TABLE)

    def write(self, trec):
        # TODO : Create a pool of records and flush them periodically instead.
        if isinstance(trec, TrafficRecord):
            with TrafficRecordDB() as db:
                values = {k: v for k, v in trec.as_dict().items() if k in self._fields}
                values['timestamp'] = trec.timestamp
                db.write(tbl=self.TABLE, **values)


class RecordManager(object):
    """
    This class act as a deamon to read traffic record queue and to
    write record to the db recorder provided
    """
    RECORD_UPDATER_THREAD_POOL_SIZE = 2

    def __init__(self, record_queue):
        self._db_recorders = [TrafficRecorder()]
        self._record_queue = record_queue
        self._stopped = threading.Event()
        self._handler = None

    def stopped(self):
        return self._stopped.is_set()

    def stop(self):
        self._stopped.set()

    def run(self):
        while not self._stopped.is_set():
            try:
                # TODO : Add logic for flush interval / buffer.
                t_record = self._record_queue.get(timeout=3)
                for recorder in self._db_recorders:
                    recorder.write(t_record)
            except Exception:
                log.error("Error in handling records")

    def start(self, blocking=False):
        self._stopped.clear()

        if blocking:
            self.run()
        else:
            self._handler = threading.Thread(target=self.run)
            self._handler.start()

    def close(self):
        self.stop()
        if self._handler:
            self._handler.join()
