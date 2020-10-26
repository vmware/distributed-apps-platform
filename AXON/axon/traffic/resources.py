#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import time


class TrafficRecord:
    """
    Class to represent TrafficRecord
    """
    TRAFFIC_TYPE = None

    def __init__(self, src, dst, port, latency,
                 error=None, success=True, connected=True):
        self.src = src
        self.dst = dst
        self.port = port
        self.latency = latency
        self.error = error[:100] if error else error
        self.success = success
        self.traffic_type = self.TRAFFIC_TYPE
        self.connected = connected
        self.created = time.time()

    def as_dict(self):
        return {
            'src': self.src, 'dst': self.dst, 'port': self.port,
            'latency': self.latency, 'error': self.error,
            'success': self.success, 'type': self.traffic_type,
            'created': self.created, 'connected': self.connected}


class TCPRecord(TrafficRecord):
    """
    TCP Traffic record
    """
    TRAFFIC_TYPE = "TCP"


class UDPRecord(TrafficRecord):
    """
    UDP Traffic Record
    """
    TRAFFIC_TYPE = "UDP"


class HTTPRecord(TrafficRecord):
    """
    HTTP Traffic Record
    """
    TRAFFIC_TYPE = 'HTTP'
