#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
Alternative / backup implementation of psutil methods consumed in lydian.
'''
import collections
import fcntl
import os
import socket
import struct
import subprocess

from lydian.apps.console import Console


def get_ipv4_address(ifname, ipv6=False):
    """
    Method for getting IP address of an interface. It would be better than
    impl below as it doesn't fork process but it doesn't work for IPv6 yet.
    """
    # _socket = socket.AF_INET6 if ipv6 else socket.AF_INET
    _socket = socket.AF_INET
    s = socket.socket(_socket, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])


def get_ip_address(ifname, ipv6=False):
    cmnd = 'ip addr show %s' % ifname
    prefix = 'inet6 ' if ipv6 else 'inet '
    try:
        status, output = Console().run_command(cmnd)
        addr = output.split(prefix)[1].split("/")[0]
    except Exception:
        addr = None
    return addr


class AddressFamily(object):
    AF_INET = 2
    AF_INET6 = 10
    AF_PACKET = 17


class snicaddr(object):
    def __init__(self, family, address):
        self.family = family
        self.address = address
        self.netmask = None
        self.broadcast = None
        self.ptp = None


def net_if_addrs():
    result = collections.defaultdict(list)
    ifnames = os.listdir('/sys/class/net/')

    for ifname in ifnames:
        for family, ipv6 in [(AddressFamily.AF_INET, False),
                             (AddressFamily.AF_INET6, True)]:
            addr = get_ip_address(ifname, ipv6)
            if addr:
                result[ifname].append(snicaddr(family=family, address=addr))

    return result


# TODO : Following need to be implemented.

class Dummy(object):
    percent = 0


dummy = Dummy()


def cpu_percent():
    """ returns system CPU Percentage utilization """
    return 0


def virtual_memory():
    """ returns system virtual memory percentage utilization """
    return dummy


def net_connections():
    """ returns number of system connections open """
    return []


class Process(object):

    def __init__(self, pid):
        self._pid = pid

    def cpu_percent(self):
        return 0

    def memory_percent(self):
        return 0

    def connections(self):
        return []


if __name__ == '__main__':
    _ = net_if_addrs()

    _ = round(cpu_percent(), 2)
    _ = round(virtual_memory().percent, 2)
    _ = int(len(net_connections()))

    p = Process(os.getpid())
    _ = round(p.cpu_percent(), 2)
    _ = round(p.memory_percent(), 2)
    _ = int(len(p.connections()))
