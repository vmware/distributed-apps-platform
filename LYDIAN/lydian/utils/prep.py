#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import argparse
import logging
import os
import re
import tempfile

from lydian.apps.config import get_param
from lydian.utils.ssh_host import Host
from lydian.utils.install import install_egg

log = logging.getLogger(__name__)

ESX = 'ESX'
UBUNTU = 'UBUNTU'
WINDOWS = 'WINDOWS'


def identify_host(result):
    if 'VMkernel' in result:
        return ESX
    elif 'Ubuntu' in result:
        # TODO : CentoS, RHEL, SUSE
        return UBUNTU
    elif 'kali' in result:
        return UBUNTU
    elif 'windows' in result:
        return WINDOWS
    else:
        return None

def get_host_type(hostip, username, password):
    with Host(host=hostip, user=username, passwd=password) as host:
        return identify_host(host.req_call('uname -a')) or \
            identify_host(host.req_call('cat /etc/os-release'))


class NodePrep(object):
    START_SERVICE = None
    STOP_SERVICE = None
    RESTART_SERVICE = None
    UNINSTALL_SERVICE = None

    # File path constants for local/source files.
    EGG_FILE = 'lydian.egg'
    SERVICE_FILE = 'lydian.service'
    CONFIG_FILE = 'lydian.conf'

    # File path constants for endpoints.
    EGG_DEST_PATH = '/root/lydian.egg'
    CONFIG_DEST_PATH = '/etc/lydian/lydian.conf'
    SERVICE_DEST_PATH = '/etc/systemd/system/lydian.service'

    DB_FILES = [
        'params.db',
        'rules.db',
        'setup.db',
        'traffic.db',
    ]

    def __init__(self, hostip, username, password):
        """
        Prepares the endpoint.
        """
        self.hostip = hostip
        self.username = username
        self.password = password

        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                     '../data')

    def prep_node(self, egg_file_src=None, cfg_path=None):
        raise NotImplementedError("'prep_node' not implemented")

    def cleanup_node(self, remove_db=False):
        raise NotImplementedError("'cleanup_node' not implemented")

    def cleanup_db(self, host):
        """
        Cleans up local DB files. Deletes file one by one, so that
        failure on one doesn't impact removal of other.
        """
        for db_file in self.DB_FILES:
            try:
                # Delete DB file and any related entries created by
                # sqlite for it.
                host.req_call('rm %s*' % db_file)
            except Exception:
                pass    # file may or may not be there.

    def run_ignore_error(self, host, cmnd):
        try:
            host.req_call(cmnd)
        except ValueError as err:
            # log.warn("cmnd: %s, error: %s", cmnd, err)    # Ignore error.
            pass

    def sync_ntp_server(self, host):
        ntp_server = get_param('LYDIAN_NTP_SERVER')
        if ntp_server:
            try:
                host.req_call('ntpdate %s' % ntp_server)
            except ValueError as err:
                log.info("Ignoring NTP synchronization error : %s", err)

    def copy_egg(self, host, egg_file_src):
        """
        Sets up Egg file at endpoint.

        Parameters
        ------------
        host: ssh_host
            SSH Host object handle.

        egg_file_src: str
            User preferred Egg file path.
        """
        egg_file = get_param('LYDIAN_EGG_PATH') or egg_file_src
        if not egg_file:
            egg_file = os.path.join(self.data_dir, self.EGG_FILE)
            if not os.path.exists(egg_file):
                # Running first time, install egg
                install_egg()
        assert os.path.exists(egg_file), "Egg file not present."
        host.put_file(egg_file, self.EGG_DEST_PATH)

    def copy_config(self, host, cfg_path):
        """
        Sets up Config file at endpoint.

        Parameters
        ------------
        host: ssh_host
            SSH Host object handle.

        cfg_path: str
            User preferred Egg file path.
        """
        config_file = get_param('LYDIAN_HOSTPREP_CONFIG') or cfg_path
        if not config_file:
            config_file = os.path.join(self.data_dir, self.CONFIG_FILE)

        host.req_call('mkdir -p /etc/lydian')
        host.put_file(config_file, self.CONFIG_DEST_PATH)

    def copy_service(self, host):
        """
        Copy Daemon service file at endpoint.

        Parameters
        ------------
        host: ssh_host
            SSH Host object handle.
        """
        service_src = os.path.join(self.data_dir, self.SERVICE_FILE)
        host.put_file(service_src, self.SERVICE_DEST_PATH)

class UbuntuNodePrep(NodePrep):

    def setup_service(self, host):
        """
        Setup service at endpoint.
        """
        python3_path = host.req_call('which python3').strip()

        # Read Service file contents
        service_file_lines = []
        with open(os.path.join(self.data_dir, self.SERVICE_FILE)) as fp:
            service_file_lines = fp.readlines()

        service_file_lines = [x if not x.startswith('ExecStart=') else
                            x % python3_path for x in service_file_lines]

        # Modify service file with python path.
        with tempfile.NamedTemporaryFile(mode='w', dir='/tmp',
                                        prefix='lydian_service_') as sfile:
            sfile.writelines(service_file_lines)
            sfile.flush()
            host.put_file(sfile.name, self.SERVICE_DEST_PATH)

    def prep_node(self, egg_file_src=None, cfg_path=None):

        with Host(host=self.hostip, user=self.username,
                  passwd=self.password) as host:
            try:
                host.req_call('systemctl stop lydian')
            except ValueError:
                pass    # preparing for first time.

            self.sync_ntp_server(host)

            # Copy Egg file
            self.copy_egg(host, egg_file_src)

            # Copy Config File.
            self.copy_config(host, cfg_path)

            # Setup daemon service.
            self.setup_service(host)

            # Start Lydian Service.
            try:
                host.req_call('sudo systemctl enable lydian.service')
                host.req_call('sudo systemctl daemon-reload')
                host.req_call('systemctl start lydian')
            except Exception as err:
                log.error("Error in starting service at %s : %r", self.hostip, err)
                return False
        return True

    def cleanup_node(self, remove_db=True):
        """
        Cleans up Lydian service from the endpoints.
        """
        with Host(host=self.hostip, user=self.username,
                  passwd=self.password) as host:
            self.run_ignore_error(host, 'systemctl stop lydian')
            self.run_ignore_error(host, 'sudo systemctl disable lydian.service')
            self.run_ignore_error(host, 'rm /etc/lydian/lydian.conf')
            self.run_ignore_error(host, 'rm /etc/systemd/system/lydian.service')
            self.run_ignore_error(host, 'rm /var/log/lydian/lydian.log')
            self.run_ignore_error(host, 'rm lydian.egg')
            if remove_db:
                self.cleanup_db(host)
        return True


class ESXNodePrep(NodePrep):
    START_SERVICE = '/etc/init.d/lydian start'
    STOP_SERVICE = '/etc/init.d/lydian stop'
    RESTART_SERVICE = '/etc/init.d/lydian restart'
    UNINSTALL_SERVICE = '/etc/init.d/lydian uninstall'

    SERVICE_FILE = 'lydian_esx.service'
    ESX_fw_cfg = 'esx_firewall.xml'
    START_SCRIPT = 'lydian_esx.sh'

    EGG_DEST_PATH = '/lydian/lydian.egg'
    SERVICE_DEST_PATH = '/etc/init.d/lydian'
    FIREWALL_XML = '/lydian/esx_fw.xml'
    FIREWALL_XML_BAK = '/lydian/esx_fw.xml.bak'

    def config_firewall(self, host):
        """
        Configures Firewall to allow connections to Lydian service from outside.
        Source : https://kb.vmware.com/s/article/2008226
        """
        xml_content = host.req_call('cat /etc/vmware/firewall/service.xml')
        if 'lydian' in xml_content:
            log.info("Firewall rule already configured on %s", self.hostip)
            return
        try:
            service_nums = set()
            result = host.req_call('grep "service id=" /etc/vmware/firewall/service.xml')
            result = result.splitlines()
            for line in result:
                try:
                    m = re.search("service id=(.+?)[ >].*", line)
                    service_nums.add(int(m.group(1)[1:-1]))
                except Exception:
                    # Hope that later higher service won't fail
                    # and we will get our service number.
                    pass
            service_num = '%s' % (max(service_nums) + 1)
        except Exception as err:
            log.error("Error in determining ESX service number for host"
                      " %s - Error: %r", self.hostip, err)
            return

        host.req_call('cp /etc/vmware/firewall/service.xml %s' % self.FIREWALL_XML_BAK)
        host.req_call('chmod 644 /etc/vmware/firewall/service.xml')
        host.req_call('chmod +t /etc/vmware/firewall/service.xml')

        # Read Firewall rule XML file contents
        fw_cfg = []
        with open(os.path.join(self.data_dir, self.ESX_fw_cfg)) as fp:
            fw_cfg = fp.readlines()

        # Update Service number
        fw_cfg = [x if not x.startswith('<service id') else
                  x % service_num.zfill(4) for x in fw_cfg]

        port_num = int(get_param('LYDIAN_PORT'))
        # Update port number
        fw_cfg = [x if '<port>' not in x else x % port_num for x in fw_cfg]

        xml_content = xml_content.splitlines()
        idx = xml_content.index("</ConfigRoot>")
        xml_content = xml_content[:idx] + fw_cfg + xml_content[idx:]

        # Modify service file with python path.
        with tempfile.NamedTemporaryFile(mode='w', dir='/tmp',
                                        prefix='lydian_esx_firewall_') as sfile:
            for line in xml_content:
                sfile.write('%s\n' % line.rstrip())
            sfile.flush()
            host.put_file(sfile.name, self.FIREWALL_XML)

        host.req_call('cp %s /etc/vmware/firewall/service.xml' % self.FIREWALL_XML)
        host.req_call('chmod 444 /etc/vmware/firewall/service.xml')
        host.req_call('chmod +t /etc/vmware/firewall/service.xml')
        host.req_call('esxcli network firewall refresh')
        # host.req_call('esxcli network firewall ruleset list') # Lydian should come in this list

    def prep_node(self, egg_file_src=None, cfg_path=None):
        with Host(host=self.hostip, user=self.username,
                  passwd=self.password) as host:
            try:
                host.req_call(self.STOP_SERVICE)
            except ValueError:
                pass    # preparing for first time.

            host.req_call('mkdir -p /lydian')

            # Copy Egg file
            self.copy_egg(host, egg_file_src)

            # Copy Config File.
            self.copy_config(host, cfg_path)

            # Copy Daemon service file.
            self.copy_service(host)

            # ESX specific steps
            host.req_call('chmod 555 %s' % self.SERVICE_DEST_PATH)

            host.put_file(os.path.join(self.data_dir, self.START_SCRIPT),
                          '/lydian/lydian.sh')
            host.req_call('chmod 555 %s' % '/lydian/lydian.sh')

            self.config_firewall(host)

            # Start Lydian Service.
            try:
                host.req_call(self.START_SERVICE, timeout=4)
            except Exception as err:
                log.error("Error in starting service at %s : %r", self.hostip, err)
                return False

        return True

    def cleanup_node(self, remove_db=True):
        """
        Cleans up Lydian service from the endpoints.
        """
        with Host(host=self.hostip, user=self.username,
                  passwd=self.password) as host:
            self.run_ignore_error(host, self.UNINSTALL_SERVICE)
            self.run_ignore_error(host, 'rm /etc/lydian/lydian.conf')
            self.run_ignore_error(host, 'rm /var/log/lydian/lydian.log')
            self.run_ignore_error(host, 'rm lydian.egg')
            if remove_db:
                self.cleanup_db(host)
        return True

    def get_running_processes(self, grep_args=None):
        """
        USAGE:
        ESXNodePrep(ip, uname, passwd).get_running_processes()
        """
        cmnd = "ps -Tcjstv"
        try:
            with Host(host=self.hostip, user=self.username,
                      passwd=self.password) as host:
                if grep_args:
                    cmnd += ' | grep %s' % grep_args
                return host.req_call(cmnd)
        except Exception as err:
            log.error("Error in running command %s at %s", cmnd, self.hostip)
            log.error("%r", err)


class WinNodePrep(NodePrep):
    pass


def get_prep_node(hostip, username, password):
    """
    Returns apporpriate node prep object based on platform type.
    """
    host_type = get_host_type(hostip, username, password)

    if host_type == UBUNTU:
        return UbuntuNodePrep(hostip, username, password)
    elif host_type == ESX:
        return ESXNodePrep(hostip, username, password)
    elif host_type == WINDOWS:
        return WinNodePrep(hostip, username, password)

    return None


def prep_node(hostip, username='root', password='FAKE_PASSWORD',
              egg_file_src=None, cfg_path=None):
    log.info("Preparing lydian at node with management IP %s", hostip)
    prep_obj = get_prep_node(hostip, username, password)
    return prep_obj.prep_node(egg_file_src, cfg_path)


def cleanup_node(hostip, username='root', password='FAKE_PASSWORD',
                 remove_db=True):
    log.info("Cleaning lydian at node with management IP %s", hostip)
    prep_obj = get_prep_node(hostip, username, password)
    return prep_obj.cleanup_node(remove_db)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-b', '--boot', taction="store_true", help='Perform Prep (boot) operation.')
    parser.add_argument(
        '-c', '--cleanup', taction="store_true", help='Perform Cleanup operation.')
    parser.add_argument(
        '-i', '--hostip', action="store_true", help="IP of host to be prepared.")
    parser.add_argument(
        '-u', '--username', action="store_true", help="Username of host.")
    parser.add_argument(
        '-p', '--password', action="store_true", help='Password of host.')


    args = parser.parse_args()

    # TODO : Allow to pass remove db , cfg file etc.
    if args.boot:
        prep_node(args.hostip, args.username, args.password)
    elif args.cleanup:
        cleanup_node(args.hostip, args.username, args.password)


if __name__ == '__main__':
    main()