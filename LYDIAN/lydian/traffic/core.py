#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
import json
import logging
import time

log = logging.getLogger(__name__)


class Target(object):
    POSIX = 'POSIX'
    NAMESPACE = 'NAMESPACE'
    CONTAINER = 'CONTAINER'
    WINVM = 'WINVM'
    HOST_TYPE = None

    def __init__(self, name=None, ip=None):
        self._name = name
        self._ip = ip    # which IP you login to run operations on.
        self._target_type = self.HOST_TYPE

    @property
    def target_type(self):
        return self._target_type

    @property
    def name(self):
        return self._name

    def is_namespace(self):
        return self.target_type == self.NAMESPACE

    def is_vmhost(self):
        """ Returns True is target is a POSIX VM """
        return self.target_type == self.POSIX

    def is_container(self):
        return self.target_type == self.CONTAINER


class VMHost(Target):
    # All POSIX VMs shall have similar way of running
    # Traffic Tasks
    HOST_TYPE = Target.POSIX


class NSHost(Target):
    # Traffic needs to be run differently in case of
    # Namespaces
    HOST_TYPE = Target.NAMESPACE


class ContainerHost(Target):
    # Container Host
    HOST_TYPE = Target.CONTAINER


class WinHost(Target):
    # Container Host
    HOST_TYPE = Target.WINVM


class TrafficRule(object):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

    SCHEMA = {
        'ruleid': 'text',       # Unique id of rule.
        'reqid': 'text',        # Request id (non unique e.g. in mesh ping)

        'src': 'text',          # source endpoint
        'dst': 'text',          # destination endpoint
        'protocol': 'text',     # Protocol : TCP/UDP/HTTP
        'port': 'text',         # port
        'connected': 'text',    # Ping expected to PASS or FAIL

        'payload': 'text',      # Payload for rule or "Dinkirk!!"
        'packet': 'text',       # Packet size for traffic.
        'tries': 'text',        # Number of tries/count of ping.

        'username': 'text',     # run traffic as. 'root' by default
        'state': 'text',        # ENABLED/DISABLED

        # Following is more of metadata. Which can be saved into
        # a separate table.
        'src_host': 'text',     # Source host Management IP
        'dst_host': 'text',     # Destination host Management IP

        'purpose':  'text',     # context : CLIENT/SERVER/PERSIST
        'target': 'text',       # Host / Namespace / Container
        }

    DEFAULTS = {
        'state': 'ACTIVE',
        'username': 'root',
        'payload': 'Dinkirk'
    }

    def fill(self):
        """ Sets the default fields if not present."""
        for key, _ in self.SCHEMA.items():
            setattr(self, key, getattr(self, key, None))

        if not self.state:
            self.state = 'ACTIVE'

        if not self.username:
            self.username = 'root'

        # At 255K rules, setting this will need 14 MB of extra memory.
        # likewise, in database, we can optimize for it.
        # if not self.payload:
        #    self.payload = 'Dinkirk!!'

    # Helper methods - Protocol(s)
    def is_TCP(self):
        return self.protocol == 'TCP'

    def is_UDP(self):
        return self.protocol == 'UDP'

    def is_HTTP(self):
        return self.protocol == 'HTTP'

    @property
    def enabled(self):
        return self.state == 'ACTIVE'

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if k in self.SCHEMA}

    def __repr__(self):
        return '%s' % self.as_dict()


class Record(object):

    def __init__(self):
        """
        Represents a Base class for recording time series data.
        """
        self._id = None
        self._timestamp = int(time.time())

    def __repr__(self):
        return '%s' % self.toJSON()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
    @property
    def timestamp(self):
        return self._timestamp

    def as_dict(self):
        return self.__dict__


class TrafficRecord(Record):

    def __init__(self):
        super(TrafficRecord, self).__init__()
        self.source = None          # ping source IP Address
        self.destination = None     # ping destination IP Address
        self.protocol = None        # ping traffic type (TCP/UDP/HTTP)
        self.port = None            # port on server where Traffic is sent.
        self.expected = None        # ping expectation (Pass/Fail : True/False)
        self.result = None          # Actual result
        self.latency = None         # ping latency
