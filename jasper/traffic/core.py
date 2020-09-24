#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
import logging

log = logging.getLogger(__name__)


class TrafficRule(object):
    SCHEMA = {
        'ruleid': 'text',       # Unique id of rule.

        'src': 'text',          # source endpoint
        'dst': 'text',          # destination endpoint
        'protocol': 'text',     # Protocol : TCP/UDP/HTTP
        'port': 'text',         # port
        'connected': 'text',    # Ping to PASS or FAIL

        'payload': 'text',      # Payload for rule.
        'packet': 'text',       # Packet size for traffic.
        'tries': 'text',        # Number of tries.

        'src_host': 'text',     # Source host Management IP
        'dst_host': 'text',     # Destination host Management IP

        'purpose':  'text',     # context : CLIENT/SERVER/PERSIST
        'username': 'text',     # run traffic as. 'root' by default
        'target': 'text',       # Host / Namespace / Container

        'state': 'text',        # ENABLED/DISABLED
        }

    DEFAULTS = {
        'state': 'ACTIVE',
        'username': 'root',
        'payload': 'Dinkirk'
    }

    def __setattr__(self, attr, val):
        if attr in self.SCHEMA:
            # super(TrafficRule, self).setattr(attr, val)
            # object.__setattr__(self, attr, val)
            self.__dict__[attr] = val
        else:
            log.error('%s is not a valid traffic rule attribute', attr)

    def fill(self):
        for key, _ in self.SCHEMA.items():
            setattr(self, key, getattr(self, key, None))

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if k in self.SCHEMA}

    def __repr__(self):
        return '%s' % self.as_dict()
