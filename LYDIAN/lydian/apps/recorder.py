#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import queue
import threading

from lydian.apps.base import BaseApp, exposify
from lydian.recorder.wf_client import WavefrontTrafficRecorder, WavefrontResourceRecorder
from lydian.traffic.core import TrafficRecord
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
            }]
        }
    VALIDATE_BEFORE_WRITE = True



class TrafficRecorder(TrafficRecordDB):
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


@exposify
class RecordManager(BaseApp):
    """
    This class act as a deamon to read traffic record queue and to
    write record to the db recorder provided
    """
    RECORD_UPDATER_THREAD_POOL_SIZE = 2
    RESOURCE_RECORD_REPORT_FREQ = 4
    TRAFFIC_RECORD_REPORT_FREQ = 4

    def __init__(self, traffic_records, resource_records):
        self._traffic_recorders = [
            TrafficRecorder(),
            WavefrontTrafficRecorder()
            ]
        self._resource_recorders = [
            WavefrontResourceRecorder()
        ]
        self._traffic_records = traffic_records
        self._resource_records = resource_records
        self._stopped = threading.Event()
        self._handlers = []

    def stopped(self):
        return self._stopped.is_set()

    def stop(self):
        self._stopped.set()

    def _traffic_record_handler(self):
        while not self._stopped.is_set():
            try:
                # TODO : Add logic for flush interval / buffer.
                t_record = self._traffic_records.get(timeout=self.TRAFFIC_RECORD_REPORT_FREQ)
                for recorder in self._traffic_recorders:
                    recorder.write(t_record)
            except queue.Empty:
                pass
            except Exception as err:
                log.error("Error in handling Traffic records : %r", err)

    def _resource_record_handler(self):
        while not self._stopped.is_set():
            try:
                # TODO : Add logic for flush interval / buffer.
                t_record = self._resource_records.get(timeout=self.RESOURCE_RECORD_REPORT_FREQ)
                for recorder in self._resource_recorders:
                    recorder.write(t_record)
            except queue.Empty:
                pass
            except Exception as err:
                log.error("Error in handling Resource records %r", err)

    def start(self, blocking=False):
        self._stopped.clear()

        # Traffic Records Handler
        thandler = threading.Thread(target=self._traffic_record_handler)
        self._handlers.append(thandler)

        # Resource Record handler
        rhandler = threading.Thread(target=self._resource_record_handler)
        self._handlers.append(rhandler)

        for handler in self._handlers:
            handler.start()

    def close(self):
        self.stop()
        _ = [h.join() for h in self._handlers]
