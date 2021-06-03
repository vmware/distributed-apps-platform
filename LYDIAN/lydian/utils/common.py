#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import ipaddress
import logging
import os
import platform
import socket

log = logging.getLogger(__name__)

system = platform.system()
is_windows = lambda: True if system == 'Windows' else False
is_linux = lambda: True if system == 'Linux' else False
is_esx = lambda: True if system == 'VMkernel' else False
is_mac = lambda: True if system == 'Darwin' else False

def is_ipv6_address(address):
    try:
        if address == 'localhost':
            _address = '127.0.0.1'
        elif address == 'ip6-localhost':
            _address = '::1'
        else:
            _address = address
        return ipaddress.ip_address(_address).version == 6
    except Exception as err:
        log.exception(err)
        log.warn("Error while trying to interprete %s as ip address.",
                 address)
        return False


def is_py3():
    return platform.python_version().startswith('3')


def get_mgmt_ifname():
    """" Management Interface name for current platform """
    if is_linux():
        return 'eth0'
    elif is_windows():
        return 'Ethernet0'
    elif is_mac():
        return 'en0'
    elif is_esx():
        return 'vmk0'


def get_host_name():
    return socket.gethostname()


def is_port_already_in_use(portnum):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', portnum))


def write_pid_file(fname):
    if not is_esx():
        return
    with open(fname, 'w+') as fp:
        fp.write('%s\n' % os.getpid())


def get_data_dir():
    """
    Returns the data dir for lydian.
    """
    return os.path.abspath(os.path.join(__file__, '../../data'))


def remove_egg(egg_name='lydian.egg'):
    """
    Removes egg file.
    """
    egg_file = os.path.join(get_data_dir(), egg_name)
    if os.path.exists(egg_file):
        os.remove(egg_file)