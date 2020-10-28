#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
This module defines Console App in AXON system.

This app shall allow running the commands on the endpoints locally. Other apps
which need to work on console such as Running traffic through other tools
(Iperf etc) or running port monioring tools shall also use/inherit this common
app.

NOTE: This should not be exposed via controller as it can pause security risk
as remote endpoints can run malicious commands using the exposed interface.
"""

import logging
import os
import shlex
import signal
import subprocess
import time

from lydian.apps.base import BaseApp

log = logging.getLogger(__name__)


class Console(BaseApp):
    NAME = "CONSOLE"

    def __init__(self):
        """
        Console App runs commands on the console of this node.
        """
        pass

    def run_command(self, cmnd, env=None, cwd=None, timeout=-1):
        """
        This function runs the command "cmnd" and returns the return code and
        result for the command. The command is taken as single string.

        Parameters
        ----------
        cmnd : string
            Command to be executed in string format.
        env : string
            Any environment configuration to be set for environment.
        cwd : string
            Absolute path to the directory where command should be run.
        timeout : int
            time in seconds after which command should be killed. Default of -1
            means command is run without a time limit.

        Returns
        -------
        (int, string)
            returns a tuple of command execution return code and output.
        """

        p = self._start_subprocess(cmnd=cmnd, cwd=cwd, env=env)

        # Start the counter for command to finish if requested.
        if timeout > 0:
            time_limit = time.time() + timeout

            while time.time() < time_limit:
                if self._is_alive(p):
                    time.sleep(1)
                else:
                    break
            self._kill_subprocess(p)

        stdout_val = p.communicate()[0]
        return p.returncode, stdout_val.strip().decode('utf-8')

    def _start_subprocess(self, cmnd,
                          stdin=None, stdout=None, stderr=None,
                          env=None, cwd=None):
        """
        Starts a subprocess and returns a handle for it.
        """
        stdout = subprocess.PIPE if not stdout else stdout
        stderr = subprocess.STDOUT if not stderr else stderr

        cmnd = shlex.split(cmnd)

        return subprocess.Popen(cmnd, shell=False, cwd=cwd, env=env,
                                stdin=stdin, stdout=stdout, stderr=stderr,
                                close_fds=True, preexec_fn=os.setsid,
                                bufsize=-1)

    def _ctrl_c(self, proc, timeout=1):
        """
        """
        proc.send_signal(signal.SIGINT)
        # For child processes, you need to wait for some time after sending
        # SIGINT signal : https://bugs.python.org/issue25942
        proc.wait(timeout)

    def _kill_subprocess(self, proc, close_fds=False):
        """
        Kills a subprocess represented by handle 'proc'.
        """
        # command is still active, kill it.
        log.warning("Killing subprocess %s" % proc.pid)
        proc.kill()
        if close_fds:
            proc.communicate()

    def _is_alive(self, proc):
        """
        Returns True if subprocess is still running else False
        """
        return proc.poll() is None
