#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

"""
Stores setup info on Primary node.
"""
import logging
import os

from lydian.apps.base import BaseApp
from lydian.apps.internal import hostinfo
from lydian.common.db import LydianDB
from lydian.controller.client import LydianClient


log = logging.getLogger(__name__)


class SetupDB(LydianDB):
    PRIMARY = 'runner'
    ENDPOINTS = 'endpoints'
    RISKS = 'risks'
    THREATS = 'threats'
    INTERFACES = 'interfaces'
    SERVICES = 'services'
    RAPIDSCAN = 'rapidscan'

    DB_SCHEMA = {
        'db_name': 'setup.db',
        'tables': [
            {
                'name': PRIMARY,
                'fields': {
                    'key': 'text',
                    'value': 'text'
                    },
                'primary_key': 'ip'
            },
            {
                'name': ENDPOINTS,
                'fields': {
                    'endpoint': 'text',
                    'hostname': 'text',
                    'host_type': 'text',
                    'mgmt_ifname': 'text',
                    'mgmt_mac': 'text',
                    'username': 'text',
                    'password': 'text'
                    },
            },
            {
                'name': INTERFACES,
                'fields': {
                    'host': 'text',
                    'ifname': 'text',
                    'ip': 'text',
                    'mac': 'text',
                    },
            },
            {
                'name': SERVICES,
                'fields': {
                    'host': 'text',
                    'service': 'text',
                    'status': 'text',
                    'description': 'text',
                    },
            },
            {
                'name': RISKS,
                'fields': {
                    'host': 'text',
                    'tool': 'text',
                    'reqid': 'text',
                    'severity': 'text',
                    'message': 'text',
                    },
            },
            {
                'name': THREATS,
                'fields': {
                    'host': 'text',
                    'severity': 'text',
                    'message': 'text',
                    },
            },
            {
                'name': RAPIDSCAN,
                'fields': {
                    'host': 'text',
                    'tool': 'text',
                    'reqid': 'text',
                    'severity': 'text',
                    'message': 'text',
                    },
            }
            ]
        }
    VALIDATE_BEFORE_WRITE = True


class SetupInfo(SetupDB, BaseApp):
    NAME = "SetupInfo"

    def add_primary_node(self):
        with SetupDB() as db:
            db.table = self.PRIMARY

            h = hostinfo.HostInfo()

            db.write(key='Host Name', value=h.hostname())
            db.write(key='Host Type', value=h.host_type())
            db.write(key='Mgmt Interface', value=h.mgmt_ifname())
            db.write(key='Mgmt IP', value=h.mgmt_ip())

    def save_endpoint(self, hostip):
        """
        # TODO : Optimize it when handling add_endpoints itself.
        """
        with SetupDB() as db:
            db.table = self.ENDPOINTS

            with LydianClient(hostip) as host:
                db.write(
                    endpoint=hostip,
                    hostname=host.hostinfo.hostname(),
                    host_type=host.hostinfo.host_type(),
                    mgmt_ifname=host.hostinfo.mgmt_ip()
                )

                db.table = self.INTERFACES

                for ifname in host.hostinfo.interfaces():
                    # TODO : Remove eth / vmk hardcode.
                    if not ifname.startswith('eth') and not ifname.startswith('vmk'):
                        continue

                    # TODO : IPv6 addresses and stabilize more below code.
                    info = host.hostinfo.iface_info(ifname) or {}
                    ip = info['address'] if 'address' in info else 'UNKNOWN'
                    db.write(
                        host=hostip,
                        ifname=ifname,
                        ip=ip
                    )

                db.table = self.SERVICES

                db.write(host=hostip,
                         service="Traffic Generation", status="ON",
                         description="Generates TCP/UDP/HTTP Traffic b/w endpoints.")

                if host.monitor.is_running():
                    db.write(host=hostip,
                             service="Resource Monitoring", status="ON",
                             description="Samples CPU/Memory usage at endpoint at fixed interval.")
