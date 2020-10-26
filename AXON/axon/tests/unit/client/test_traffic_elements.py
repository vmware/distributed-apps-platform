#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from axon.tests import base as test_base
from axon.client.traffic_elements import InvalidRangeError, \
    InvalidPortError, InvalidRuleError
from axon.client.traffic_elements import TrafficRule, Protocol, \
    Connected, Action, Port, Endpoint


class TestTrafficElements(test_base.BaseTestCase):
    """
    Test for TrafficElements utilities
    """

    def test_valid_endpoint_elements(self):
        self.traffic_element = TrafficRule(Endpoint('1.2.3.4'),
                                           Endpoint('2.3.4.5'),
                                           Port(12345),
                                           Protocol.UDP,
                                           Connected.CONNECTED,
                                           Action.ALLOW)
        self.assertIsInstance(self.traffic_element.src_eps, Endpoint)
        self.traffic_element.__repr__()

    def test_invalid_src_element(self):
        try:
            self.traffic_element = TrafficRule(Endpoint('1.2.3.4444'),
                                               Endpoint('2.3.4.5'),
                                               Port(12345),
                                               Protocol.UDP,
                                               Connected.CONNECTED,
                                               Action.ALLOW)
        except InvalidRangeError:
            pass
        except Exception as e:
            raise RuntimeError('Wrong exception is raised - %s' % e)

    def test_invalid_dst_element(self):
        try:
            self.traffic_element = TrafficRule(Endpoint('1.2.3.4'),
                                               Endpoint('2.3.4.5555'),
                                               Port(12345),
                                               Protocol.UDP,
                                               Connected.CONNECTED,
                                               Action.ALLOW)
        except InvalidRangeError:
            pass
        except Exception as e:
            raise RuntimeError('Wrong exception is raised - %s' % e)

    def test_invalid_port_element(self):
        try:
            self.traffic_element = TrafficRule(Endpoint('1.2.3.4'),
                                               Endpoint('2.3.4.5'),
                                               Port(123456),
                                               Protocol.UDP,
                                               Connected.CONNECTED,
                                               Action.ALLOW)
        except InvalidPortError:
            pass
        except Exception as e:
            raise RuntimeError('Wrong exception is raised - %s' % e)

    def test_invalid_protocol_element(self):
        try:
            self.traffic_element = TrafficRule(Endpoint('1.2.3.4'),
                                               Endpoint('2.3.4.5'),
                                               Port(12345),
                                               'FAKE_PROTOCOL',
                                               Connected.CONNECTED,
                                               Action.ALLOW)
        except InvalidRuleError:
            pass
        except Exception as e:
            raise RuntimeError('Wrong exception is raised - %s' % e)

    def test_invalid_collected_element(self):
        try:
            self.traffic_element = TrafficRule(Endpoint('1.2.3.4'),
                                               Endpoint('2.3.4.5'),
                                               Port(12345),
                                               'TCP',
                                               'FAKE_CONNECTED',
                                               Action.ALLOW)
        except InvalidRuleError:
            pass
        except Exception as e:
            raise RuntimeError('Wrong exception is raised - %s' % e)

    def test_invalid_action_element(self):
        try:
            self.traffic_element = TrafficRule(Endpoint('1.2.3.4'),
                                               Endpoint('2.3.4.5'),
                                               Port(12345),
                                               'TCP',
                                               True,
                                               'FAKE_ACTION')
        except InvalidRuleError:
            pass
        except Exception as e:
            raise RuntimeError('Wrong exception is raised - %s' % e)
