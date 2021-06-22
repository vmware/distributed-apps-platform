#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from collections import defaultdict
import logging
import multiprocessing
import platform
import re
import subprocess

if "Linux" in platform.uname():  # noqa
    from lydian.utils import nsenter

import lydian.common.errors as errors

try:
    import psutil
except errors.ModuleNotFoundError:
    import lydian.utils.lpsutil as psutil
from lydian.apps import config


INTERFACE_FAMILY = (2, 10)

NAMESPACE_INTERFACE_NAME_PREFIXES = config.get_param('NAMESPACE_INTERFACE_NAME_PREFIXES')

log = logging.getLogger(__name__)


def get_interfaces_in_namespace(return_dict):
    return_dict['result'] = psutil.net_if_addrs()
    return return_dict


class Namespace(object):
    """
    Namespace object which holds information name, id, interfaces inside
    """
    def __init__(self, name, id=None):
        self._name = name
        self._id = id
        self._interface_list = []
        self.discover_interfaces()

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def interfaces(self):
        return self._interface_list

    def as_dict(self):
        return dict(list(zip(['name', 'id', 'interfaces'],
                        [self.name, self.id, [interface.as_dict() for
                                              interface in self.interfaces]])))

    def discover_interfaces(self):
        ns_path = '/var/run/netns/%s' % self.name
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        with nsenter.namespace(ns_path, 'net'):
            process = multiprocessing.Process(
                target=get_interfaces_in_namespace, args=(return_dict,))
            process.start()
            process.join()
        for name, snics in list(return_dict['result'].items()):
            for nic in [snic for snic in snics if snic.family in INTERFACE_FAMILY]:
                self._interface_list.append(Interface(
                    name, nic.address, nic.family,
                    nic.netmask, nic.broadcast))


class NamespaceManager(object):
    """
    Class that controls all relevant NS on a machine
    - upon launch, discovers all namespaces
    - provide apis to get all the necessary information
    """

    def __init__(self):
        self._namespace_map = {}
        self._namespace_interface_map = {}
        self._linux_distro = "Linux" in platform.uname()
        self.discover_namespaces()

    def discover_namespaces(self):
        if self._linux_distro:
            ns_list = subprocess.check_output(["ip", "netns", "list"])
            if not ns_list:
                return
            for ns in ns_list.decode().rstrip().split("\n"):
                ns_name, ns_id = None, None
                try:
                    lindex = ns.index(' ')
                    ns_name = ns[:lindex]
                    ns_id = re.findall('[0-9]+', ns[lindex:])[0]
                except Exception as err:
                    log.error("Cannot parse Namespace info for %s - %r", ns, err)
                    continue

                _ns = Namespace(ns_name, ns_id)
                self._namespace_map[ns_name] = _ns
                interfaces = _ns.interfaces
                self._namespace_interface_map[ns_name] = interfaces or None

    def get_namespace_interface_map(self):
        return self._namespace_interface_map

    def get_all_namespaces(self):
        """
        Get the list of all namespaces presnt in the system
        :return: List of namespace names
        :rtype: list
        """
        return list(self._namespace_map.keys())

    def get_namespace(self, namespace):
        ns = self._namespace_map.get(namespace)
        if ns:
            return ns.as_dict()
        else:
            return None

    def get_all_namespaces_ips(self):
        """
        Get the list of all namespaces ips address present in the system
        based on NAMESPACE_INTERFACE_NAME_PREFIXES
        :return: List of namespace ips
        :rtype: list
        """
        namespaces_ips = []
        for np in list(self._namespace_map.values()):
            interfaces = [iface for iface in np.interfaces for prefix in
                          NAMESPACE_INTERFACE_NAME_PREFIXES
                          if prefix in iface.name]
            if not interfaces:
                continue
            for iface in interfaces:
                namespaces_ips.append(iface.address)

        return namespaces_ips


class Interface(object):
    """
    Interface object which holds all the information related to interface
    """
    def __init__(self, name, address, family, netmask, broadcast):
        self._name = name
        self._address = address
        self._family = family
        self._netmask = netmask
        self._broadcast = broadcast

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def family(self):
        return self._family

    @property
    def netmask(self):
        return self._netmask

    @property
    def broadcast(self):
        return self._broadcast

    def as_dict(self):
        return dict(list(zip(['name', 'address', 'family', 'netmask', 'broadcast'],
                        [self.name, self.address, self.family, self.netmask,
                         self.broadcast])))


class InterfaceManager(object):
    """
    Class that controls all Interface information on host
    """
    def __init__(self):
        self.discover_interfaces()

    def discover_interfaces(self):
        self._interface_map = defaultdict(list)
        addrs = psutil.net_if_addrs()
        for name, snics in list(addrs.items()):
            for nic in [snic for snic in snics if snic.family in INTERFACE_FAMILY]:
                self._interface_map[name].append(
                    Interface(name, nic.address, nic.family, nic.netmask,
                              nic.broadcast))

    def get_all_interfaces(self):
        """
        Get all the interface names present in the system
        :return:
        :rtype:
        """
        return list(self._interface_map.keys())

    def get_interface(self, name, ip=None):
        """
        Get detail about a particular interface
        :param name: name of the interface
        :type name: str
        :param ip: IPv4 or IPv6 address to be matched
        :type ip: str
        :return: interface object as dict
        :rtype: dict
        """
        snics = self._interface_map.get(name)
        if not snics:
            return None
        for snic in snics:
            if not ip:
                # Return the first interface found in snics if IP address is not
                # provided
                return snic.as_dict()
            else:
                if snic.address == ip:
                    return snic.as_dict()

    def get_interface_by_ip(self, ip):
        for name, interface in list(self._interface_map.items()):
            for sub_interface in interface:
                if sub_interface.address == ip:
                    return name

    def get_ips_by_interface(self, interface):
        ips = []
        if interface not in self._interface_map:
            return ips
        for sub_interface in self._interface_map.get(interface):
            ips.append(sub_interface.address)
        return ips

    def get_all_ips(self):
        all_ips = []
        all_interfaces = self.get_all_interfaces()
        for interface in all_interfaces:
            all_ips.extend(self.get_ips_by_interface(interface))
        return all_ips

iface_mgr = None
ns_mgr = None

def get_interface_manager():
    global iface_mgr
    if not iface_mgr:
        iface_mgr = InterfaceManager()
    return iface_mgr

def get_ns_manager():
    global ns_mgr
    if not ns_mgr:
        ns_mgr = NamespaceManager()
    return ns_mgr