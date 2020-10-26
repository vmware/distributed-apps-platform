#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
Unit test for Iperf app.
'''
import logging
import time
import unittest
import warnings


from axon.apps.iperf import Iperf


log = logging.getLogger(__name__)


class TestIperfApp(unittest.TestCase):

    def setUp(self):
        super(TestIperfApp, self).setUp()
        self._app = Iperf()
        warnings.simplefilter('ignore', category=ResourceWarning)

    def test_iperfApp(self):
        """
        Test iperf server / client / supporting APIs
        """
        _server_ports = [7011, 7012, 7013]
        _client_jobs = []
        _running_ports = []
        _test_duration = 10

        # start iperf server on given port
        for port in _server_ports:
            assert self._app.start_iperf_server(port) == port

        # start iperf server on random port
        assert isinstance(self._app.start_iperf_server(), int)

        _running_ports = self._app.get_server_ports()
        assert _running_ports

        # start iperf clients
        for port in _running_ports:
            _client_jobs.append(self._app.start_iperf_client('localhost', port,
                                                             duration=_test_duration))

        assert _client_jobs
        time.sleep(_test_duration)

        # check client job info
        for job in _client_jobs:
            job_info = self._app.get_client_job_info(job)
            assert job_info.get('popen_obj')
            assert job_info.get('state') in ('running', 'done')
            if job_info.get('state') == 'done':
                assert job_info.get('result')
            assert job_info.get('cmd')

        # Stop iperf server running on different ports
        for port in self._app.get_server_ports():
            self._app.stop_iperf_server(port)
            assert not self._app.is_running(port)
