#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import pickle

from lydian.apps.base import BaseApp, exposify
from lydian.utils.network_utils import get_interface_manager


@exposify
class InterfaceApp(BaseApp):
    def __init__(self):
        self._if_mngr = get_interface_manager()

    def list_interfaces(self):
        return self._if_mngr.get_all_interfaces()

    def get_interface(self, name, ip=None):
        return self._if_mngr.get_interface(name, ip)

    def get_all_ips(self):
        return self._if_mngr.get_all_ips()

    def get_ips_by_interface(self, interface):
        return self._if_mngr.get_ips_by_interface(interface)

    def get_interface_ips_map(self):
        result = {}
        for iface in self.list_interfaces():
            result[iface] = self.get_ips_by_interface(iface)
        return pickle.dumps(result)
