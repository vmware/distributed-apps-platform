#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import sys
import time

from axon.client.traffic_elements import TrafficRule, \
    Endpoint, Port, Protocol, Action, Connected
from axon.client.basic_traffic_controller import BasicTrafficController
from axon.client.axon_client import AxonClient


class BasicL2ConnectivityTest(object):
    """
    Basic L2 Connectivity Test.
    """
    def __init__(self, managed_hosts):
        self.log = logging.getLogger(__name__)
        self.managed_hosts = managed_hosts

    def _create_allow_rules_on_hosts(self, source, destinations):
        rule_list = []
        for destination in destinations:
            rule_list.append(TrafficRule(Endpoint(source),
                             Endpoint(destination),
                             Port(12345), Protocol.TCP,
                             Connected.CONNECTED, Action.ALLOW))
            rule_list.append(TrafficRule(Endpoint(source),
                             Endpoint(destination),
                             Port(12345), Protocol.UDP,
                             Connected.CONNECTED, Action.ALLOW))
            rule_list.append(TrafficRule(Endpoint(source),
                             Endpoint(destination), Port(5432), Protocol.TCP,
                             Connected.CONNECTED, Action.ALLOW))
            rule_list.append(TrafficRule(Endpoint(source),
                             Endpoint(destination), Port(5432), Protocol.UDP,
                             Connected.CONNECTED, Action.ALLOW))
        return rule_list

    def create_rules_with_given_hosts(self):
        """
        Params:
        managed_hosts: list of hosts which can access each other
        """
        rule_list = []
        for index, host in enumerate(self.managed_hosts):

            # Form simplicity we are considering each host is sending
            # traffic to other 10 destinations
            managed_destinations = (self.managed_hosts
                                    [:index][::-1][:5] + self.managed_hosts
                                    [index + 1: index + 6])
            allow_rules = self._create_allow_rules_on_hosts(
                host, managed_destinations)
            rule_list.extend(allow_rules)
        return rule_list


if __name__ == "__main__":
    managed_hosts = sys.argv[1:]
    if not managed_hosts:
        print("\nHELP: python test.py <host1> <host2> . . <hostN>\n")
        sys.exit()
    basic_test_obj = BasicL2ConnectivityTest(managed_hosts)
    traffic_rules = basic_test_obj.create_rules_with_given_hosts()
    controller = BasicTrafficController()
    controller.register_traffic(traffic_rules)
    controller.restart_traffic()
    start_time = time.time()
    time.sleep(30)
    end_time = time.time()
    for host in managed_hosts:
        with AxonClient(host) as client:
            print("Checking failure count for host - %s" % host)
            failure_count = client.stats.get_failure_count(
                start_time=start_time, end_time=end_time)
            success_count = client.stats.get_success_count(
                start_time=start_time, end_time=end_time)
            print("Failure Count = %s " % failure_count)
            print("sucess Count = %s " % success_count)
            if failure_count != 0:
                raise RuntimeError("Traffic is failing."
                                   "Failure count for "
                                   "host %s is %s" % (host, failure_count))
