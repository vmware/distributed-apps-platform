#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import json
import uuid
import time


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


class ResourceRecord(Record):

    def __init__(self, syscpu=None, sysmem=None, sysconns=None,
                 lydiancpu=None, lydianmem=None, lydianconns=None):
        super(ResourceRecord, self).__init__()
        self.syscpu = syscpu
        self.sysmem = sysmem
        self.sysconns = sysconns
        self.lydiancpu = lydiancpu
        self.lydianmem = lydianmem
        self.lydianconns = lydianconns


class TrafficRecord(Record):

    def __init__(self):
        super(TrafficRecord, self).__init__()
        self.source = None          # ping source IP Address
        self.destination = None     # ping destination IP Address
        self.protocol = None           # ping traffic type (TCP/UDP/HTTP)
        self.expected = None        # ping expectation (Pass/Fail : True/False)
        self.result = None          # Actual result
