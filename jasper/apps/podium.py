#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import threading
import time

from jasper.apps.base import BaseApp, exposify
from jasper.utils.common import get_mgmt_ifname, get_host_name
from jasper.utils.prep import prep_node
from jasper.controller.client import LydianClient

import jasper.common.consts as consts


log =logging.getLogger(__name__)

_podium = None


@exposify
class Podium(BaseApp):

    TENNAT_VM_USERNAME = 'root'
    TENNAT_VM_PASSWORD = '!cisco'

    HOST_WAIT_TIME = 4

    def __init__(self, username=None, password=None):
        """
        Podium app for running the show.
        # TODO : Add persistence to Podium app.
        """
        self._primary = True
        self._ep_hosts = {}
        self._ep_username = username or self.TENNAT_VM_USERNAME
        self._ep_password = password or self.TENNAT_VM_PASSWORD

    @property
    def endpoints(self):
        return self._ep_hosts.keys()

    def wait_on_host(self, hostip, wait_time=None):
        wait_time = wait_time or self.HOST_WAIT_TIME
        et = int(time.time() + wait_time)

        while time.time() < et:
            if self.is_host_up(hostip):
                return True

        return False

    def add_endpoints(self, hostip, username=None, password=None):
        """
        Add endpoints from the host, reachable by hostip.
        """
        if hostip in self.endpoints:
            log.info("%s is already added.", hostip)
            return

        username = username or self._ep_username
        password = password or self._ep_password

        try:
            with LydianClient(hostip) as client:
                # fetch regular interfaces
                for iface in client.interface.list_interfaces():
                    if not any([iface.startswith(x) for x in
                                consts.NAMESPACE_INTERFACE_NAME_PREFIXES]):
                        continue
                    ips = client.interface.get_ips_by_interface(iface)
                    for ip in ips:
                        self._ep_hosts[ip] = hostip

                # Fetch Namespace Interfaces
                for ip in client.namespace.list_namespaces_ips():
                    self._ep_hosts[ip] = hostip

            self._ep_hosts[hostip] = hostip

        except Exception as err:
            log.error("Error in adding endpoint %s - %r", hostip, err)

    def add_hosts(self, hostip, username=None, password=None):
        username = username or self._ep_username
        password = password or self._ep_password
        try:
            prep_node(hostip, username, password)
            if not self.wait_on_host(hostip):
                log.error("Could not start service on %s", hostip)
            self.add_endpoints(hostip, username, password)
        except Exception as err:
            log.error("Error in preparing host %s - %r", hostip, err)

    def is_host_up(self, hostip):
        try:
            with LydianClient(hostip) as client:
                client.monitor.is_running()
            return True
        except Exception:
            return False

    def get_ep_host(self, epip):
        return self._ep_hosts.get(epip, None)

    def register_traffic(self, intent):
        # TODO : Optimization opportunities
        # Club all requests to same host in one call.
        for rule in intent:
            srchost = self.get_ep_host(rule['src'])
            dsthost = self.get_ep_host(rule['dst'])

            if not srchost:
                log.error("No host found for running traffic from IP : %s",
                          rule['src'])
                continue
            elif not dsthost:
                log.error("No host found for running traffic from IP : %s",
                          rule['dst'])
                continue

            # Start Server before the client.
            with LydianClient(dsthost) as dclient:
                dclient.controller.register_traffic([rule])

            with LydianClient(srchost) as sclient:
                sclient.controller.register_traffic([rule])


def get_podium():
    global _podium
    if not _podium:
        _podium = Podium()

    return _podium
