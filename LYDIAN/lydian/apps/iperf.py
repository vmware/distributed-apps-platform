#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
App for running iperf server or client.
"""
import logging
import random
import time

from lydian.apps.base import BaseApp, exposify
import lydian.apps.console as console

log = logging.getLogger(__name__)

@exposify
class Iperf(console.Console):

    IPERF_BIN = 'iperf3'
    _START_RAND_PORT = 5600
    _END_RAND_PORT = 6000
    _STARTING_JOB_ID = 1000

    def __init__(self):
        super(Iperf, self).__init__()
        # {<port>: <popen obj>}
        self._server_handles = {}

        # {<job_id>: {'popen_obj': <popen obj>,
        #             'state': 'running' | 'done',
        #             'result': < None | JSON output>,
        #             'cmd': <command>
        #             }
        self._client_handles = {}
        self._job_id = None
        self._gen_rand_port = self._gen_rand_port(self._START_RAND_PORT,
                                                  self._END_RAND_PORT)

    def start_iperf_server(self, port=None, args=''):
        """
        Start iperf server on given port. If port is not
        provided, random port will be used.

        :param port: (int) TCP port number (default: None)
        :param args: (str) Additional iperf supported args
        :return:
        port: (int) TCP port number being used for iperf server
        """
        if not port:
            port = next(self._gen_rand_port)
        if self.is_running(port):
            log.info("Server is already running on port: %d"
                     "Skip starting server." % port)
            return port
        cmd = self.IPERF_BIN + ' ' + '-s -p %s' % str(port)
        if args:
            cmd += ' ' + args
        p = self._start_subprocess(cmd)
        # Check server is running
        for _ in range(3):
            if self.is_running(port):
                self._server_handles[port] = p
                log.info("Server is running on port:%d " % port)
                break
            time.sleep(1)
        else:
            msg = "unable to start iperf3 server. check port:%d is available." % port
            log.error(msg)
            raise RuntimeError(msg)
        return port

    def _gen_rand_port(self, start_port, end_port):

        for _ in range(start_port, end_port + 1):
            port = random.randint(start_port, end_port)
            if port not in self._server_handles:
                yield port
        else:
            msg = "Running out of random port between starting port: %d - "\
                             "ending port: %d" % (start_port, end_port)
            log.error(msg)
            raise ValueError(msg)

    def get_server_ports(self):
        """
        Get running server ports.
        :return:
        list of currently running server ports
        """
        return [p for p in self._server_handles.keys()]

    def stop_iperf_server(self, port):
        """
        Stop iperf server for given port.
        """
        proc = self._server_handles.get(port)
        if proc:
            self._kill_subprocess(proc)
            self._server_handles.pop(port)

    def stop_iperf_client(self, job_id):
        """
        Stop iperf client for given job_id.
        """
        job = self._client_handles.get(job_id)
        if job:
            self._kill_subprocess(job.get('popen_obj'))
            self._client_handles.pop(job_id)

    def start_iperf_client(self, dst_ip, dst_port, duration=10, udp=False,
                           bandwidth=None, args=''):
        """
        Start iperf client to given dst_ip and port.

        :param dst_ip: (str) IP address of iperf server
        :param dst_port: (int) iperf server port to connect to
        :param dst_port: (int) iperf server port to connect to
        :param duration: (int) test duration
        :param udp: (bool) enable udp
        :param bandwidth: (int)  limit traffic to as much Mbits/second
        :return:
        job_id: (int)
        """

        cmd = self.IPERF_BIN + ' ' + '-c %s -p %s -t %s' % (str(dst_ip),
                                                            str(dst_port),
                                                            str(duration))
        cmd += ' ' + '--json'
        if udp:
            cmd += " --udp"
            # iperf3 udp default is 1 Mbit/s, this sets it to unlimited / 10Gb/s
            if not bandwidth:
                bandwidth = 10240
        if bandwidth:
            cmd += " --bandwidth %dM" % bandwidth
        if args:
            cmd += ' ' + args
        p = self._start_subprocess(cmd)
        self._job_id = self._STARTING_JOB_ID if not self._job_id \
            else self._job_id + 1

        self._client_handles[self._job_id] = {'popen_obj': p,
                                              'state': 'running',
                                              'result': None,
                                              'cmd': cmd}
        log.info("cmd: %s running with job_id: %s" % (cmd, self._job_id))
        return self._job_id

    def get_client_jobs(self):
        return [j for j in self._client_handles.keys()]

    def get_client_job_info(self, job_id):
        """
        Get client job info on given job id.

        :param job_id: (int)
        :return:
        job_details: (dict)
            # {'popen_obj': <popen obj>,
            #  'state': 'running' | 'done',
            #  'result': < None | JSON output>,
            #  'cmd': <command>
            # }
        """
        if job_id not in self._client_handles:
            log.error("Job ID:%d not found" % job_id)
            return None
        p = self._client_handles[job_id].get('popen_obj')
        if not self._is_alive(p):
            if self._client_handles[job_id].get('result') is None:
                result_json = p.communicate()[0].decode('utf-8')
                result_json = result_json.replace('\n', '').replace('\t', '')
                self._client_handles[job_id]['result'] = result_json
            self._client_handles[job_id]['state'] = 'done'

        return self._client_handles[job_id]

    def stop(self):
        """
        Stop iperf app.
        """
        server_ports = self.get_server_ports()
        client_jobs = self.get_client_jobs()

        for port in server_ports:
            log.info("Stopping iperf server on port %s", port)
            proc = self._server_handles.get(port)
            if proc:
                self._kill_subprocess(proc)

        for job_id in client_jobs:
            log.info("Stopping iperf client process for job: %s" % job_id)
            proc = self._client_handles[job_id].get('popen_obj')
            if proc:
                self._kill_subprocess(proc)

    def is_running(self, port):
        """
        Check iperf server is running on given port
        """
        netstat = self._start_subprocess('netstat -lnp')
        grep = self._start_subprocess('grep :%s' % port, stdin=netstat.stdout)
        netstat.stdout.close()  # Allow netstat to receive a SIGPIPE if grep exits.
        output = grep.communicate()[0].decode('utf-8')
        return self.IPERF_BIN in output
