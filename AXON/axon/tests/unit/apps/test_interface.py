#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock
from psutil._common import snicaddr

from axon.tests import base as test_base
from axon.apps.interface import InterfaceApp


class TestInterfaceApp(test_base.BaseTestCase):
    """
        Unit Tests for InterfaceApp utilities
    """
    def setUp(self):
        super(TestInterfaceApp, self).setUp()
        self.interface = {'bridge0': [snicaddr(
            family=2, address='7a:00:4d:60:d1:00',
            netmask=None, broadcast=None, ptp=None)]}

    @mock.patch('psutil.net_if_addrs')
    def test_list_interfaces(self, mock_if_addrs):
        mock_if_addrs.return_value = self.interface
        self._interface_app = InterfaceApp()
        result = self._interface_app.list_interfaces()
        mock_if_addrs.assert_called()
        self.assertIn('bridge0', result)

    @mock.patch('psutil.net_if_addrs')
    def test_get_existing_interfaces(self, mock_if_addrs):
        mock_if_addrs.return_value = self.interface
        self._interface_app = InterfaceApp()
        result = self._interface_app.get_interface('bridge0')
        mock_if_addrs.assert_called()
        self.assertEqual(result['name'], 'bridge0')

    @mock.patch('psutil.net_if_addrs')
    def test_get_non_existing_interfaces(self, mock_if_addrs):
        mock_if_addrs.return_value = self.interface
        self._interface_app = InterfaceApp()
        result = self._interface_app.get_interface('bridge1')
        mock_if_addrs.assert_called()
        self.assertIsNone(result)
