# !/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock

from axon.tests import base as test_base
from axon.utils.network_utils import NamespaceManager
from axon.apps.namespace import NamespaceApp


class TestNamespaceApp(test_base.BaseTestCase):
    """
        Unit Tests for NameSpaceApp utilities
    """
    def setUp(self):
        super(TestNamespaceApp, self).setUp()
        self._namespace_app = NamespaceApp()

    @mock.patch.object(NamespaceManager, 'get_all_namespaces')
    def test_list_namespaces(self, mock_ns):
        mock_ns.return_value = ['test_ns']
        result = self._namespace_app.list_namespaces()
        mock_ns.assert_called()
        self.assertIn('test_ns', result)

    @mock.patch.object(NamespaceManager, 'get_namespace')
    def test_get_namespace(self, mock_ns):
        mock_ns.return_value = 'fake-ns-details'
        result = self._namespace_app.get_namespace('fake_ns')
        mock_ns.assert_called_with('fake_ns')
        self.assertEqual(result, 'fake-ns-details')

    @mock.patch.object(NamespaceManager, 'get_all_namespaces_ips')
    def test_list_namespaces_ips(self, mock_ns):
        mock_ns.return_value = ['1.2.3.4']
        result = self._namespace_app.list_namespaces_ips()
        mock_ns.assert_called()
        self.assertEqual(result, ['1.2.3.4'])
