#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
# Author : Fred Grim, Vipin Sharma
"""
A standalone utility for connecting to hosts through paramiko over SSH.
"""
import collections
import io
import logging
import os
import pkgutil
import platform
import time

import paramiko


FakeProc = collections.namedtuple('FakeProc', ['stdin', 'stdout', 'stderr'])

def is_py3():
    return platform.python_version().startswith('3')


class Host(object):
    """
    A host that implements the minimum required interface for copying the
    egg file over to a remote machine.

    Parameters
    ----------
    host : string
        The host to connect to
    user : string, optional
        The username to connect as
    passwd : string, optional
        The password for the connecting user
    keyfile : string, optional
        A local keyfile that can authenticate this against this host
    connect : bool, optional
        Connect on instantiation ? or no ?
    """
    AUTOMATION_KEY_NAME = 'automation_rsa'
    REPLY_BUFFER = 2 ** 11  # bytes
    CONNECT_RETRY_LIMIT = 5
    CONNECT_RETRY_SLEEP = 30
    log = logging.getLogger(__name__)

    def __init__(self, host, user=None, passwd=None, keyfile=None,
                 connect=True):
        self.__host = host
        self.__ssh = paramiko.SSHClient()
        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._connected = False
        self.__connect_kwargs = {'look_for_keys': False}
        if user is not None:
            self.__connect_kwargs['username'] = user
        if passwd is not None:
            self.__connect_kwargs['password'] = passwd
        if keyfile is not None:
            self.__connect_kwargs['key_filename'] = keyfile
        else:
            kfile = os.path.join('remote_data', self.AUTOMATION_KEY_NAME)
            kfile_abspath = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), kfile)
            if os.path.exists(kfile_abspath):
                keydata = pkgutil.get_data(__name__, kfile)
                pkey_file = io.BytesIO(keydata)
                from_pkey_cb = paramiko.rsakey.RSAKey.from_private_key
                self.__connect_kwargs['pkey'] = from_pkey_cb(pkey_file)
        if connect:
            self.ssh_connect()

    def ssh_connect(self):
        attempts, ssh_exc = 0, None
        while attempts < self.CONNECT_RETRY_LIMIT:
            try:
                self.__ssh.connect(self.__host, **self.__connect_kwargs)
                self._connected = True
                return
            except Exception as exc:
                ssh_exc = exc
                self.log.error('Re-connecting to %s due to %s' % (
                    self.__host, str(ssh_exc)))
                time.sleep(self.CONNECT_RETRY_SLEEP)
                attempts += 1
        self.log.error('Connecting to %s failed like %s' % (
            self.__host, str(ssh_exc)))

    def get_sftp_connection(self):
        attempts = 0
        sftp_client = None
        while attempts < self.CONNECT_RETRY_LIMIT:
            try:
                sftp_client = self.__ssh.open_sftp()
                break
            except Exception as exc:
                self.log.warn("Retrying after sftp failure %s" % exc)
                attempts += 1
        return sftp_client

    @property
    def connected(self):
        return self._connected

    @property
    def ip(self):
        """
        The original host supported this.
        """
        return self.__host

    def put_file(self, src, dst=None):
        """
        This puts the file on the remote host

        Parameters
        ----------
        src : string
            The local file
        dst : string, optional
            The destination path.  If it none the file is dumped in /tmp
        """
        if dst is None:
            dst = os.path.join('/tmp', os.path.basename(src))
        self.log.debug('%s put_file %s %s' % (self.__host, src, dst))
        sftp_client = self.get_sftp_connection()
        try:
            sftp_client.put(src, dst)
        finally:
            sftp_client.close()

    def get_file(self, src, dst=None):
        """
        This gets the file from the remote host

        Parameters
        ----------
        src : string
            The remote file
        dst : string, optional
            The destination path.  If it none the file is dumped in /tmp
        """
        if dst is None:
            dst = os.path.join('/tmp', os.path.basename(src))
        self.log.debug('%s get_file %s %s' % (self.__host, src, dst))
        sftp_client = self.get_sftp_connection()
        try:
            sftp_client.get(src, dst)
        finally:
            sftp_client.close()

    def check_file_exists(self, path):
        """
        Check that a file exists on the remote node

        Parameters
        ----------
        path : string
            The remote path to check
        """
        self.log.debug('%s check_file_exists %s' % (self.__host, path))
        sftp_client = self.get_sftp_connection()
        try:
            return sftp_client.stat(path).st_mtime > 0
        except IOError:
            return False
        finally:
            sftp_client.close()

    def req_call(self, cmd, msg=None, expected_ret=None, timeout=None):
        """
        This mimics the dynamics of req_call

        Parameters
        ----------
        cmd : string
            The command to call
        msg : string, optional
            ignored
        expected_ret : string, optional
            ignored
        """
        _, _ = msg, expected_ret  # pylint
        self.log.debug('%s req_call %s' % (self.__host, cmd))
        attempts, ssh_exc = 0, None
        chan = None
        while attempts < self.CONNECT_RETRY_LIMIT:
            try:
                chan = self.__ssh.get_transport().open_session()
                break
            except Exception as exc:
                ssh_exc = exc
                time.sleep(self.CONNECT_RETRY_SLEEP)
                attempts += 1
                self.log.error('Re-connecting to %s failed like %s' % (
                    self.__host, ssh_exc.message))

        if chan is not None:
            try:
                if timeout:
                    chan.settimeout(timeout)
                chan.exec_command(cmd)
                if chan.recv_exit_status() != 0:
                    raise ValueError(
                        'Nonzero exit status on %s stderr = %s' % (
                            cmd, chan.recv_stderr(self.REPLY_BUFFER)))
                reply = ''
                while True:
                    chunk = chan.recv(self.REPLY_BUFFER)
                    chunk = chunk.decode('utf-8') if is_py3() else chunk
                    if chunk == '':
                        break
                    else:
                        reply += chunk 
                return reply
            finally:
                    chan.close()

    @staticmethod
    def check_return(proc):
        """
        noop
        """
        pass

    def delete_file(self, path, force=False, check=True):
        """
        The removes a file on the host

        Parameters
        ----------
        path : string
            The path to remove
        force : boolean, optional
            Force the removal, defaults to rais eexception on fail
        check : boolean, optional
            Check that the file exists
        """
        _ = check  # make pylint happy
        self.log.debug('%s delete_file %s' % (self.__host, path))
        sftp_client = self.get_sftp_connection()
        try:
            sftp_client.remove(path)
        except IOError:
            if force:
                pass
            else:
                raise
        finally:
            sftp_client.close()

    call = req_call

    def run_command(self, cmd):
        """
        Run a command and return something that looks like the results of a
        subprocess.Popen

        Parameters
        ----------
        cmd : string
            The command to run
        """
        chan = self.__ssh.get_transport().open_session()
        try:
            chan.exec_command(cmd)
            stdout, stderr = io.BytesIO(), io.BytesIO()
            _ = chan.recv_exit_status()
            for callback, fobj in [(chan.recv, stdout),
                                   (chan.recv_stderr, stderr)]:
                while True:
                    chunk = callback(self.REPLY_BUFFER)
                    _chunk = chunk.decode('utf-8') if is_py3() else chunk
                    if _chunk == '':
                        break
                    else:
                        fobj.write(chunk)
                fobj.seek(os.SEEK_SET)
            return FakeProc(io.BytesIO(), stdout, stderr)
        finally:
            chan.close()

    req_command = run_command

    def wait_ready(self):
        """
        Wait until the command is complete. Noop
        """
        return True

    def close(self):
        self.__ssh.close()
        self._connected = False

    def __str__(self):
        return '<%s %s>' % (self.__class__.__name__, self.ip)

    def __repr__(self):
        return '<%s %s at 0x%x>' % (
            self.__class__.__name__, self.ip, id(self))

    def __enter__(self):
        if not self.connected:
            self.ssh_connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()


class LocalHost(Host):
    """
    This just runs commands on the localhost
    """

    def __init__(self, user=None, passwd=None, keyfile=None):
        super(LocalHost, self).__init__(
            '127.0.0.1', user=user, passwd=passwd, keyfile=keyfile)

