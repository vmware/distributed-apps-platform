#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock
import time

from axon.apps.stats import StatsApp
from axon.db.sql.repository import TrafficRecordsRepositery
from axon.tests import base as test_base


class TestStatsApp(test_base.BaseTestCase):
    """
        Test for StatsApp utilities
    """

    def setUp(self):
        super(TestStatsApp, self).setUp()
        self._stats_app = StatsApp()

    @mock.patch('axon.db.sql.analytics.session_scope')
    @mock.patch.object(TrafficRecordsRepositery, 'get_record_count')
    def test_get_failure_count(self, mock_rc, mock_session):
        mock_rc.return_value = 10
        mock_session.side_effect = None
        start_time = time.time()
        end_time = start_time + 10
        destination = '1.2.3.4'
        port = 12345
        result = self._stats_app.get_failure_count(
            start_time=start_time,
            end_time=end_time,
            destination=destination,
            port=port)
        mock_rc.assert_called()
        self.assertEqual(10, result)

    @mock.patch('axon.db.sql.analytics.session_scope')
    @mock.patch.object(TrafficRecordsRepositery, 'get_record_count')
    def test_get_success_count(self, mock_rc, mock_session):
        mock_rc.return_value = 10
        mock_session.side_effect = None
        start_time = time.time()
        end_time = start_time + 10
        destination = '1.2.3.4'
        port = 12345
        result = self._stats_app.get_success_count(
            start_time=start_time,
            end_time=end_time,
            destination=destination,
            port=port)
        mock_rc.assert_called()
        self.assertEqual(10, result)

    @mock.patch('axon.db.sql.analytics.session_scope')
    @mock.patch.object(TrafficRecordsRepositery, 'get_records')
    def test_get_failures(self, mock_records, mock_session):
        mock_records.return_value = 'fake_failures'
        mock_session.side_effect = None
        start_time = time.time()
        end_time = start_time + 10
        destination = '1.2.3.4'
        port = 12345
        result = self._stats_app.get_failures(
            start_time=start_time,
            end_time=end_time,
            destination=destination,
            port=port)
        mock_records.assert_called()
        self.assertEqual('fake_failures', result)
