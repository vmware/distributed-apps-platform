#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import argparse
import logging
import os
import tempfile

from lydian.apps.config import get_configs
from lydian.utils.ssh_host import Host
from lydian.utils.install import install_egg

log = logging.getLogger(__name__)


def prep_node(hostip, username='root', password='FAKE_PASSWORD',
              egg_file_src=None, cfg_path=None):

    config = get_configs()

    with Host(host=hostip, user=username, passwd=password) as host:
        try:
            host.req_call('systemctl stop lydian')
        except ValueError:
            pass    # preparing for first time.

        data_dir = os.path.dirname(os.path.realpath(__file__))

        # Copy service file
        python3_path = host.req_call('which python3').strip()

        # Read Service file contents
        service_file_lines = []
        with open(os.path.join(data_dir, '../data/lydian.service')) as fp:
            service_file_lines = fp.readlines()

        service_file_lines = [x if not x.startswith('ExecStart=') else
                              x % python3_path for x in service_file_lines]

        # Modify service file with python path.
        with tempfile.NamedTemporaryFile(mode='w', dir='/tmp',
                                         prefix='lydian_service_') as sfile:
            sfile.writelines(service_file_lines)
            sfile.flush()
            host.put_file(sfile.name, '/etc/systemd/system/lydian.service')

        # Copy Egg file
        egg_file = config.get_param('LYDIAN_EGG_PATH') or egg_file_src
        if not egg_file:
            egg_file = os.path.join(data_dir, '../data/lydian.egg')
            if not os.path.exists(egg_file):
                # Running first time, install egg
                install_egg()
        assert os.path.exists(egg_file), "Egg file not present."
        host.put_file(egg_file, '/root/lydian.egg')

        # Copy Config File.
        config_file = config.get_param('LYDIAN_HOSTPREP_CONFIG') or cfg_path
        if not config_file:
            config_file = os.path.join(data_dir, '../data/lydian.conf')

        host.req_call('mkdir -p /etc/lydian')
        host.put_file(config_file, '/etc/lydian/lydian.conf')

        try:
            host.req_call('sudo systemctl enable lydian.service')
            host.req_call('sudo systemctl daemon-reload')
            host.req_call('systemctl start lydian')
        except Exception as err:
            log.error("Error in starting service at %s : %r", hostip, err)
            return False
    return True


def cleanup_node(hostip, username='root', password='FAKE_PASSWORD', remove_db=True):
    """
    Cleans up Lydian service from the endpoints.
    """

    with Host(host=hostip, user=username, passwd=password) as host:

        def _func(cmnd):
            try:
                host.req_call(cmnd)
            except ValueError as err:
                log.warn("cmnd: %s, error: %s", cmnd, err)
        _func('systemctl stop lydian')
        _func('sudo systemctl disable lydian.service')
        _func('rm /etc/lydian/lydian.conf')
        _func('rm /etc/systemd/system/lydian.service')
        _func('rm /var/log/lydian/lydian.log')
        if remove_db:
            _func('rm traffic.db params.db rules.db')


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
