#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
Generic Results app. Gives results for traffic operations.
'''

import logging
import pickle

from lydian.apps.base import BaseApp, exposify
from lydian.apps.recorder import TrafficRecordDB


log = logging.getLogger(__name__)


@exposify
class Results(BaseApp):

    def traffic(self, reqid, **kwargs):
        _filter = {}
        for key, value in kwargs.items():
            if key in TrafficRecordDB.SCHEMA:
                _filter[key] = value
            else:
                log.info("Skipping invalid TrafficRecord key:%s", key)

        result = []
        with TrafficRecordDB() as db:
            result = db.read(tbl=db.TABLE, reqid=reqid, **_filter)

        return pickle.dumps(result)

    def traffic_records_count(self, **kwargs):
        """
        Returns total number of records in traffic database.
        """
        count = None
        with TrafficRecordDB() as db:
            count = db.count(tbl=db.TABLE, **kwargs)
        return count

    def get_latency_stat(self, reqid, method, **kwargs):
        _filter = {}
        for key, value in kwargs.items():
            if key in TrafficRecordDB.SCHEMA:
                _filter[key] = value
            else:
                log.info("Skipping invalid TrafficRecord key:%s", key)

        result = None
        with TrafficRecordDB() as db:
            if method == 'avg':
                result =  db.avg(field='latency', tbl=db.TABLE, reqid=reqid, **_filter)
            elif method == 'min':
                result = db.min(field='latency', tbl=db.TABLE, reqid=reqid, **_filter)
            elif method == 'max':
                result = db.max(field='latency', tbl=db.TABLE, reqid=reqid, **_filter)
            else:
                log.error("Invalid method: %s for getting latency stat.", method)

        return result

    def get_avg_latency(self, reqid, **kwargs):
        return self.get_latency_stat(reqid, method='avg', **kwargs)

    def get_min_latency(self, reqid, **kwargs):
        return self.get_latency_stat(reqid, method='min', **kwargs)

    def get_max_latency(self, reqid, **kwargs):
        return self.get_latency_stat(reqid, method='max', **kwargs)

    def delete_record(self, reqid, **kwargs):
        with TrafficRecordDB() as db:
            db.delete(tbl=db.TABLE, reqid=reqid, **kwargs)
