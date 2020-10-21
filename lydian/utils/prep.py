#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import argparse
import logging
import os
import tempfile

from lydian.utils.ssh_host import Host
from lydian.utils.pack import generate_egg

log = logging.getLogger(__name__)


def prep_node(hostip, username='root', password='FAKE_PASSWORD'):

    with Host(host=hostip, user=username, passwd=password) as host:
        try:
            host.req_call('systemctl stop lydian')
        except ValueError:
            pass    # preparing for first time.

        data_dir = os.path.dirname(os.path.realpath(__file__))
        # Copy service file
        service_file = os.path.join(data_dir, '../data/lydian.service')

        host.put_file(service_file,
                      '/etc/systemd/system/lydian.service')

        # Copy Egg file
        egg_file = os.path.join(data_dir, '../data/lydian.egg')
        host.put_file(egg_file, '/tmp/lydian.egg')

        # Copy Config File.
        config_file = os.path.join(data_dir, '../data/lydian.conf')
        host.req_call('mkdir -p /etc/lydian')
        host.put_file(config_file, '/etc/lydian/lydian.conf')

        host.req_call('mv /tmp/lydian.egg ~/')
        try:
            host.req_call('sudo systemctl enable lydian.service')
            host.req_call('sudo systemctl daemon-reload')
            host.req_call('systemctl start lydian')
        except Exception as err:
            log.error("Error in starting service at %s : %r", hostip, err)
            return False
    return True


def cleanup_node(hostip, username='root', password='FAKE_PASSWORD'):
    """
    Cleans up Lydian service from the endpoints.
    """

    with Host(host=hostip, user=username, passwd=password) as host:

        def _func(cmnd):
            try:
                host.req_call(cmnd)
            except ValueError:
                pass
        _func('systemctl stop lydian')
        _func('sudo systemctl disable lydian.service')
        _func('rm /etc/lydian/lydian.conf')
        _func('rm /etc/systemd/system/lydian.service')
        _func('rm /var/log/lydian/lydian.log')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--hostip', action="store_true", help="IP of host to be prepared.")
    parser.add_argument(
        '-u', '--username', action="store_true", help="Username of host.")
    parser.add_argument(
        '-p', '--password', taction="store_true", help='Password of host.')

    args = parser.parse_args()
    prep_node(args.hostip, args.username, args.password)


if __name__ == '__main__':
    main()
