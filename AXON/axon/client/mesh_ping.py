#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import argparse
import six
import sys

import ipaddress

from axon.client.utils import create_mesh_ping_topo_from_cidr
from axon.client.basic_traffic_controller import BasicTrafficController


def build_parser():
    parser = argparse.ArgumentParser(description='Mesh Ping Generator')
    parser.add_argument('--cidr', dest='cidr', action='store',
                        help="cidr where traffic should be generated")
    return parser


def start_traffic(cidr):
    network = ipaddress.ip_network(six.text_type(cidr)).hosts()
    rule_list = create_mesh_ping_topo_from_cidr(list(network))
    controller = BasicTrafficController()
    controller.register_traffic(rule_list)
    controller.restart_traffic()


def main():
    parser = build_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    start_traffic(args.cidr)


if __name__ == "__main__":
    sys.exit(main())
