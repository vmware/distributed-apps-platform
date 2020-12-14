#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
Mock module to mimic functionality so as LYDIAN service doesn't go
down when a particular component/package is down or not available.
'''

class DeadNode(object):
    def __init__(self, *args, **kwargs):
        """
        A Dead class which does nothing but mainly to be consumed
        for handling resiliency issues.
        """
        pass

class DummyWaveFrontWriter(DeadNode):
    def write(self, rec):
        pass

WavefrontTrafficRecorder = DummyWaveFrontWriter

WavefrontResourceRecorder = DummyWaveFrontWriter

class WavefrontDeadClient(DeadNode):

    def sender(self, *args, **kwargs):
        pass

WavefrontDirectClient = WavefrontDeadClient

WavefrontProxyClient = WavefrontDeadClient