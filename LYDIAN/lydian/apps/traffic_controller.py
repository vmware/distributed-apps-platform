#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

'''
Traffic Controller App handles all the pre processing and post processing
work for Traffic Generation.
'''
import pickle
import logging

from lydian.apps.base import BaseApp, exposify

import lydian.traffic.core as core
import lydian.traffic.task as task

from lydian.utils.network_utils import get_ns_manager, get_interface_manager, \
        NAMESPACE_INTERFACE_NAME_PREFIXES

from lydian.traffic.manager import ClientManager, ServerManager
from lydian.utils import parallel
from lydian.utils.common import get_mgmt_ifname, get_host_name


log = logging.getLogger(__name__)

@exposify
class TrafficControllerApp(BaseApp):

    def __init__(self, record_queue, rulesApp, traffic_tools):
        super(TrafficControllerApp, self).__init__()

        self._recore_queue = record_queue
        self.rules = rulesApp
        self.traffic_tools = traffic_tools

        # TODO : Following should be consumed through Global Apps actually.
        # Namespace Manager handles all namespace information fetching.
        self._ns_mgr = get_ns_manager()
        # Interface Manager
        self._if_mgr = get_interface_manager()
        # Endpoint - Target Map. A target can be host, Namespace or
        # a container.

        # Host is where this app is running. Based on host,
        # it is decided for a rule if we need to run a client
        # or server.
        ifname = get_mgmt_ifname()
        self._host = self._if_mgr.get_interface(ifname)['address']
        self._update_endpoints_map()

        self._client_mgr = ClientManager(self._recore_queue)
        self._server_mgr = ServerManager()

        # Resume Active rules
        self._resume_active_rules()

    @property
    def host(self):
        return self._host

    def _get_traffic_tool(self, trule):
        if trule.tool not in self.traffic_tools:
            log.error("Unrecognized tool - %s for rule %r", trule.tool, trule)
            return None
        return self.traffic_tools[trule.tool]

    def _update_endpoints_map(self):
        self._ep_map = {}

        # Update Interfaces on this host
        host_target = core.VMHost(name=get_host_name(),
                                  ip=self.host)

        # To support local traffic.
        self._ep_map['127.0.0.1'] = host_target
        self._ep_map['::1'] = host_target

        for ifname in self._if_mgr.get_all_interfaces():
            if not any([ifname.startswith(x) for x in NAMESPACE_INTERFACE_NAME_PREFIXES]):
                continue
            ips = self._if_mgr.get_ips_by_interface(ifname)
            for ip in ips:
                self._ep_map[ip] = host_target

        # Update Namespaces on this host.
        for ns_name, ns_interfaces in self._ns_mgr.get_namespace_interface_map().items():
            ns_target = core.NSHost(name=ns_name, ip=self.host)
            for interface in ns_interfaces:
                self._ep_map[interface.address] = ns_target

    def discover_interfaces(self):
        """ Re/Discovers insterfaces """
        self._if_mgr.discover_interfaces()
        self._ns_mgr.discover_namespaces()
        self._update_endpoints_map()

    def _add_rule_info(self, trule):
        trule.src_target = self._ep_map.get(trule.src)
        trule.dst_target = self._ep_map.get(trule.dst)
        trule.src_host = self.host if trule.src_target else None
        trule.dst_host = self.host if trule.dst_target else None

        if not trule.src_host and not trule.dst_host:
            log.error("Invalid request to add rule (%s) on host %s",
                      trule, self.host)
            return

        # Set Active/Inactive State
        trule.state = getattr(trule, 'state', core.TrafficRule.ACTIVE)

        if trule.external:
            # Handle traffic rule through 3rd party tool.
            traffic_tool = self._get_traffic_tool(trule)
            if traffic_tool:
                traffic_tool.register_traffic([trule])
        else:
            # Handle rule by internal traffic handlers.
            # Add server on this host if needed. Start server before the client.
            if trule.dst_host:
                self._server_mgr.add_task(trule)

            # Add client on this host if needed.
            if trule.src_host:
                self._client_mgr.add_task(trule)

    def _get_traffic_rule(self, rule):
        """ Rule config. """
        log.info("Processing rule : %s", rule)
        trule = core.TrafficRule()

        for key, val in rule.items():
            setattr(trule, key, val)

        self._add_rule_info(trule)
        return trule

    def register_traffic(self, traffic_rules=None):
        try:
            traffic_rules = pickle.loads(traffic_rules)
        except Exception:
            # unpickled data. Let the error be raised later
            # if we cann't process it.
            pass    # unpickled data.
        log.info("Registering Traffic : %r", traffic_rules)
        _trules = []
        for rule in traffic_rules:
            # create a rule and add it to database.
            trule = self._get_traffic_rule(rule)
            _trules.append(trule)

        self.rules.add_rules(_trules)
        log.info("Registered Traffic Successfully: %r", traffic_rules)

    def register_rule(self, trule):
        try:
            trule = pickle.loads(trule)
        except Exception:
            # unpickled data. Let the error be raised later
            # if we cann't process it.
            pass    # unpickled data.

        log.info("Registering Traffic : %r", trule)
        self._add_rule_info(trule)
        self.rules.add(trule)
        log.info("Registered Traffic Successfully: %r", trule)
        return trule

    def _start(self, ruleid):
        """ Start a Traffic task (again). """
        trule = self.rules.rules.get(ruleid, None)
        if not trule:
            log.error("Unable to find rule for id:%s", ruleid)
        elif trule.enabled:
            log.info("Traffic task for %s already started.", trule.ruleid)
        elif trule.external:
            traffic_tool = self._get_traffic_tool(trule)
            if traffic_tool:
                traffic_tool.start_traffic(trule)
                self.rules.enable(ruleid)
        else:
            # Enable the trule
            self.rules.enable(ruleid)
            self._client_mgr.start(trule)

    def _stop(self, ruleid):
        """ Stop a Traffic task. """
        trule = self.rules.rules.get(ruleid, None)
        if not trule:
            log.error("Unable to find rule for id:%s", ruleid)
        elif not trule.enabled:
            log.info("Traffic task for %s already stopped.", trule.ruleid)
        elif trule.external:
            traffic_tool = self._get_traffic_tool(trule)
            if traffic_tool:
                traffic_tool.stop_traffic(trule)
                self.rules.disable(ruleid)
        else:
            self._client_mgr.stop(trule)
            # Disable the trule
            self.rules.disable(ruleid)
            # Servers are not stopped as other traffic rules still might
            # need them. TODO : Do reference counting.

    def start(self, rules):
        if not isinstance(rules, list):
            rules = [rules]
        args = [(ruleid, (ruleid,), {}) for ruleid in rules]
        parallel.ThreadPool(self._start, args)

    def stop(self, rules, blocking=True):
        if not isinstance(rules, list):
            rules = [rules]
        args = [(ruleid, (ruleid,), {}) for ruleid in rules]
        if blocking:
            parallel.ThreadPool(self._stop, args)
        else:
            # NOTE : Pre-mature exit can lead to zombie threads and can cause
            # eventual degradation of resources at endpoints. For this reason
            # stop and other operations are blocking.
            parallel.ThreadPool(self._stop, args)

    def unregister_traffic(self, rules):
        """ Stop traffic and delete rules from db"""
        if not isinstance(rules, list):
            rules = [rules]
        self.stop(rules)
        self.rules.delete_rules(rules)

    def _resume_active_rules(self):
        active_rules = [rule for ruleid, rule in self.rules.rules.items()
                        if rule.state == self.rules.ACTIVE]
        log.info("Restarting traffic on rules : %s",
                 ','.join([x.ruleid for x in active_rules]))

        # Starting all ACTIVE rules
        for trule in active_rules:
            self._add_rule_info(trule)

    def close(self):
        self._client_mgr.close()
        self._server_mgr.close()
