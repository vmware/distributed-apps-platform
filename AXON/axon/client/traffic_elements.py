#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
This module represents the elements of Traffic inside the Traffic Controller.
All the definitions of traffic node and elements must be specified here. This
acts as the single point of control for putting constraints around the things
like type of traffic protocols to support, range of ports allowed, type of src
/dest IP representations to expect. It also helps in avoiding the cyclic
dependency.
'''
import ipaddress
import json
import six


class Error(Exception):
    pass


class InvalidRangeError(Error):
    """
    Exception raised when IP address range is incorrect.
    """
    pass


class InvalidRuleError(Error):
    """
    Exception raised when Traffic rule is invalid.
    """
    pass


class InvalidPortError(Error):
    """
    Exception for Invalid Port number. Valid port numers are in the range of
    0 - 65555 only but if we want a more fine grained control, it would be the
    place to do that (for Traffic Controller).
    """
    pass


class ProtocolError(object):
    """
    Invalid protocol exception raised for AddOn Traffic.
    """
    pass


class Endpoint(object):

    def __init__(self, ep_address):
        """
        This class represents a valid recognizable endpoint address.
        Endpoint address can be one of the following
            - IP address,
            - CIDR representation.
        """
        self.ep_address = ep_address
        self.ip_list = self.expand_iprange(ep_address)

    def expand_iprange(self, ep_address):
        """
        This method takes string representation as an input and expands it
        into the list of IP addresses if a valid input.
        """
        try:
            return list(ipaddress.ip_network(six.text_type(ep_address)))
        except Exception as err:
            raise InvalidRangeError(err)

    def __repr__(self):
        return '%r' % self.ip_list


class EndpointList(object):

    def __init__(self, ep_addresses):
        """
        This class represents a valid recognizable endpoint address.
        Endpoint address can be one of the following
            - list of IP addresses,
            - list of CIDR representation.
        """
        self.ep_addresses = ep_addresses
        self.ip_list = self.expand_iprange(ep_addresses)

    def expand_iprange(self, ep_address):
        """
        This method takes string representation as an input and expands it
        into the list of IP addresses if a valid input.
        """
        ip_list = []
        for ep_address in self.ep_addresses:
            try:
                ip_list.append(list(ipaddr.IPNetwork(
                    six.text_type(ep_address))))
            except Exception as err:
                raise InvalidRangeError(err)
        return ip_list

    def __repr__(self):
        return '%r' % self.ip_list


class Port(object):
    PORT_START = 1
    PORT_MAX = 65555

    def __init__(self, port):
        """
        This class represents 'Port' withing Traffic Controller system.
        """
        try:
            assert(port > self.PORT_START and port < self.PORT_MAX)
            self._port = int(port)
        except Exception as err:
            raise InvalidPortError(err)

    @property
    def port(self):
        return self._port

    def toJSON(self):
        return json.dumps(self.port)

    def __repr__(self):
        return '%s' % self.port


class Protocol(object):
    """
    This class enlists and controls all the protocols supported and handled
    by the Traffic Controller system.
    """
    TCP = "TCP"
    UDP = "UDP"
    HTTP = "HTTP"

    allowed = [TCP, UDP, HTTP]


class Action(object):
    """
    This class enlists and controls all the actions allowed on different
    traffic rules.

    NOTE: In future we might want to grow this list to handle more refined
    response checking such as :
        - Host unreachable.
        - Port in use.
        - Permission Denied etc.
    """
    DROP = 0
    ALLOW = 1

    allowed = [DROP, ALLOW]


class Connected(object):
    """
    This class tell whether two endpoints are connected or not
    """
    CONNECTED = True
    DISCONNECTED = False

    allowed = [CONNECTED, DISCONNECTED]


class TrafficRule(object):

    def __init__(self, src, dst, port, protocol=Protocol.TCP,
                 connected=Connected.CONNECTED, action=Action.ALLOW):
        """
        This class captures the notion of Traffic Rule or Traffic Command for
        the Traffic Controller system. A Traffic rule/command can specify :
            - Traffic from 'source' to 'destination' on 'port' for 'protocol'
              is 'allowed/denied'

              -OR-

            - Start listening for 'protocol' type traffic at 'port' on the
              'destination' endpoint.
        """
        try:
            # A rule must have destination endpoint , protocol and port.
            assert src or dst, "At least src or dst must not be None."
            if src is not None:
                assert(isinstance(src, Endpoint) or
                       isinstance(src, EndpointList)), "src must be instance of EndPoint"
            if dst is not None:
                assert(isinstance(dst, Endpoint) or
                    isinstance(dst, EndpointList)), "dst must be instance of EndPoint"
            assert(isinstance(port, Port)), "port must be instance of Port"
            assert(action in Action.allowed), "Invalid Action"
            assert (connected in Connected.allowed), "Invalid Connected"
            assert(protocol in Protocol.allowed), "Invalid Protocol"

            self.src_eps = src
            self.dst_eps = dst
            self.protocol = protocol
            self.port = port
            self.action = action
            self.connected = connected

        except Exception as err:
            raise InvalidRuleError(err)

    def __repr__(self):
        return '%s %s traffic on port %s from %s to  %s.' % (
               'ALLOW' if self.action else 'DROP',
               self.protocol, self.port,
               self.src_eps, self.dst_eps)
