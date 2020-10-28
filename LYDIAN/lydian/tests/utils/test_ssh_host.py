#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
import os
import tempfile
import unittest

import lydian.utils.ssh_host as ssh_host


# To rn this test case, swap line 16 and 17 and set the credentials
# on the machine you are running it at.

# class SSHHostTest(unittest.TestCase):
class SSHHostTest(object):

    USERNAME = ''
    PASSWORD = ''   # Avoid exposing on public github

    def test_run_command(self):
        """
        Test SSH Client ability to connect , run commands and drop connection
        at close.
        """
        host = ssh_host.LocalHost(user=self.USERNAME, passwd=self.PASSWORD)
        assert host.connected
        assert host.req_call('hostname')
        assert host.req_call('ls -lrt')
        assert host.req_call('pwd')
        host.close()
        assert not host.connected

    def test_file_put_get(self):
        """
        Test SSH Client ability to copy file via sftp connection.
        """
        with tempfile.TemporaryDirectory(dir='/tmp') as tdir:
            tfile = os.path.join(tdir, 'hello.txt')
            with open(tfile, 'w+') as fp:
                fp.write("Hello world!")

            with ssh_host.LocalHost(user=self.USERNAME,
                                    passwd=self.PASSWORD) as host:
                dest = os.path.join(tdir, 'hello_copy.txt')

                host.put_file(tfile, dest)  # Put file through SFTP.
                assert  host.check_file_exists(dest)

                copy2 = os.path.join(tdir, 'hello_get.txt')
                host.get_file(dest, copy2)  # get file through SFTP.

            with open(tfile, 'r') as fp:
                orig_data = fp.readlines()

            with open(dest, 'r') as fp:
                copy_data = fp.readlines()

            with open(copy2, 'r') as fp:
                get_data = fp.readlines()

            assert orig_data == copy_data
            assert orig_data == get_data

    def test_context(self):
        """
        Test SSH Client ability to connect to host, run commands and drop
        connection at the end of context automatically.
        """
        with ssh_host.LocalHost(user=self.USERNAME,
                passwd=self.PASSWORD) as host:
            assert host.req_call('hostname')
            assert host.req_call('ls -lrt')
            assert host.req_call('pwd')

        assert not host.connected
