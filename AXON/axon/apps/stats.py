#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import time

from axon.db.sql.analytics import session_scope
from axon.db.sql.repository import Repositories


class StatsApp(object):
    def __init__(self):
        self._repository = Repositories()

    def _set_time_range(self, start_time=None, end_time=None):
        if not end_time:
            end_time = time.time()
        if not start_time:
            start_time = end_time - 300
        return start_time, end_time

    def _set_scope(self, start_time=None, end_time=None,
                  destination=None, port=None, source=None):
        start_time, end_time = self._set_time_range(start_time, end_time)
        filters = {}
        if port:
            filters['port'] = port
        if destination:
            filters['dst'] = destination
        if source:
            filters['src'] = source

        return start_time, end_time, filters

    def get_traffic_stats(self, start_time=None, end_time=None):
        start_time, end_time = self._set_time_range(start_time, end_time)

        with session_scope() as session:
            return self._repository.request_count.get_request_count(
                session, start_time, end_time)

    def get_avg_latency(self, start_time=None, end_time=None):
        start_time, end_time = self._set_time_range(start_time, end_time)

        with session_scope() as session:
            return self._repository.latency.get_latency_stats(
                session, start_time, end_time)


    def get_failure_count(self, start_time=None, end_time=None,
                          destination=None, port=None, source=None):
        start_time, end_time, filters = self._set_scope(start_time, end_time,
                                                        destination, port,
                                                        source)
        with session_scope() as session:
            return self._repository.fault.get_record_count(
                session, start_time, end_time, **filters)

    def get_success_count(self, start_time=None, end_time=None,
                          destination=None, port=None, source=None):
        start_time, end_time, filters = self._set_scope(start_time, end_time,
                                                        destination, port,
                                                        source)
        with session_scope() as session:
            return self._repository.record.get_record_count(
                session, start_time, end_time, **filters)

    def get_failures(self, start_time=None, end_time=None,
                     destination=None, port=None, source=None):
        start_time, end_time, filters = self._set_scope(start_time, end_time,
                                                        destination, port,
                                                        source)
        with session_scope() as session:
            return self._repository.fault.get_records(
                session, start_time, end_time, **filters)

    def get_successes(self, start_time=None, end_time=None,
                      destination=None, port=None, source=None):
        start_time, end_time, filters = self._set_scope(start_time, end_time,
                                                        destination, port,
                                                        source)
        with session_scope() as session:
            return self._repository.record.get_records(
                session, start_time, end_time, **filters)
