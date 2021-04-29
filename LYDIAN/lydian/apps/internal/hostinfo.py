#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import os
import pickle

from lydian.apps.base import BaseApp, exposify
from lydian.apps.console import Console
from lydian.utils.common import get_host_name, get_mgmt_ifname
from lydian.utils.network_utils import InterfaceManager

ESX = 'ESX'
KALI = 'KALI'
UBUNTU = 'UBUNTU'
WINDOWS = 'WINDOWS'

@exposify
class HostInfo(BaseApp):
    def __init__(self):
        self._if_mngr = InterfaceManager()
        self._hostname = get_host_name()
        self._mgmt_ifname = get_mgmt_ifname()
        self._mgmt_ip = self._if_mngr.get_interface(self._mgmt_ifname)['address']

        _, result = Console().run_command('uname -a')
        if 'VMkernel' in result:
            self._host_type = ESX
        elif 'Ubuntu' in result:
            self._host_type = UBUNTU
        elif 'kali' in result:
            self._host_type = KALI
        elif 'windows' in result or 'CYGWIN_NT' in result:
            self._host_type = WINDOWS
    def hostname(self):
        return self._hostname

    def mgmt_ifname(self):
        return self._mgmt_ifname

    def mgmt_ip(self):
        return self._mgmt_ip

    def host_type(self):
        return self._host_type

    # TODO : provide only one way to fetch info. 
    # Either here or through Interface Manager.
    def iface_info(self, ifname):
        return self._if_mngr.get_interface(self._mgmt_ifname)

    def interfaces(self):
        return self._if_mngr.get_all_interfaces()
