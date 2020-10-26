#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.


import mock

from rpyc import Service
from rpyc.utils.server import ThreadPoolServer

from axon.tests import base as test_base
from axon.controller.axon_rpyc_controller import main, AxonController


class TestAxonController(test_base.BaseTestCase):
    """
    Test for AxonController utilities
    """

    def setUp(self):
        super(TestAxonController, self).setUp()
        self._local_setup()

    @mock.patch('rpyc.utils.server.ThreadPoolServer.__init__')
    def _local_setup(self, mock_server_init):
        with mock.patch('axon.db.sql.config.models.Base.metadata.create_all')\
                as mock_db_conn:
            mock_db_conn.return_value = None
            mock_server_init.return_value = None
            self.axon_controller = AxonController()

    @mock.patch('axon.controller.axon_rpyc_controller.AxonController.start')
    @mock.patch('rpyc.utils.server.ThreadPoolServer.__init__')
    def test_main(self, mock_server_init, mock_start):
        with mock.patch('axon.db.sql.config.models.Base.metadata.create_all')\
                as mock_db_conn:
            mock_db_conn.return_value = None
            mock_server_init.return_value = None
            mock_start.return_value = None
            main()

    def test_axon_controller_init(self):
        self.assertTrue(isinstance(self.axon_controller.service, Service))
        self.assertTrue(isinstance(self.axon_controller.axon_service,
                                   ThreadPoolServer))

    @mock.patch.object(ThreadPoolServer, 'start')
    def test_start(self, mock_start):
        mock_start.return_value = None
        self.axon_controller.start()

    @mock.patch.object(ThreadPoolServer, 'close')
    def test_stop(self, mock_close):
        mock_close.return_value = None
        self.axon_controller.stop()
