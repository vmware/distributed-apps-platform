#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import time

from lydian.apps.base import BaseApp, exposify
from lydian.utils.prep import prep_node
from lydian.controller.client import LydianClient

import lydian.common.consts as consts


log = logging.getLogger(__name__)

_podium = None


def _get_host_ip(host, func_ip=None):
    func = lambda vm: vm.ip
    func_ip = func if func_ip is None else func_ip
    return func_ip(host)


@exposify
class Podium(BaseApp):

    TENNAT_VM_USERNAME = 'root'
    TENNAT_VM_PASSWORD = '!cisco'

    HOST_WAIT_TIME = 4

    def __init__(self, username=None, password=None):
        """
        Podium app for running the show.
        # TODO : Add persistence to Podium app.
        """
        self._primary = True
        self._ep_hosts = {}
        self._ep_username = username or self.TENNAT_VM_USERNAME
        self._ep_password = password or self.TENNAT_VM_PASSWORD

    @property
    def endpoints(self):
        return self._ep_hosts.keys()

    def wait_on_host(self, hostip, wait_time=None):
        wait_time = wait_time or self.HOST_WAIT_TIME
        et = int(time.time() + wait_time)

        while time.time() < et:
            if self.is_host_up(hostip):
                return True

        return False

    def add_endpoints(self, hostip, username=None, password=None):
        """
        Add endpoints from the host, reachable by hostip.
        """
        if hostip in self.endpoints:
            log.info("%s is already added.", hostip)
            return

        username = username or self._ep_username
        password = password or self._ep_password

        try:
            with LydianClient(hostip) as client:
                # fetch regular interfaces
                for iface, ips in client.interface.get_interface_ips_map().items():
                    if not any([iface.startswith(x) for x in
                                consts.NAMESPACE_INTERFACE_NAME_PREFIXES]):
                        continue
                    for ip in ips:
                        self._ep_hosts[ip] = hostip

                # Fetch Namespace Interfaces
                for ip in client.namespace.list_namespaces_ips():
                    self._ep_hosts[ip] = hostip

            self._ep_hosts[hostip] = hostip

        except Exception as err:
            log.error("Error in adding endpoint %s - %r", hostip, err)

    def add_hosts(self, hostip, username=None, password=None):
        username = username or self._ep_username
        password = password or self._ep_password
        try:
            prep_node(hostip, username, password)
            if not self.wait_on_host(hostip):
                log.error("Could not start service on %s", hostip)
            self.add_endpoints(hostip, username, password)
        except Exception as err:
            log.error("Error in preparing host %s - %r", hostip, err)

    def is_host_up(self, hostip):
        try:
            with LydianClient(hostip) as client:
                client.monitor.is_running()
            return True
        except Exception:
            return False

    def get_ep_host(self, epip):
        return self._ep_hosts.get(epip, None)

    def register_traffic(self, intent):
        # TODO : Optimization opportunities
        # Club all requests to same host in one call.
        for rule in intent:
            srchost = self.get_ep_host(rule['src'])
            dsthost = self.get_ep_host(rule['dst'])

            if not srchost:
                log.error("No host found for running traffic from IP : %s",
                          rule['src'])
                continue
            elif not dsthost:
                log.error("No host found for running traffic from IP : %s",
                          rule['dst'])
                continue

            # Start Server before the client.
            with LydianClient(dsthost) as dclient:
                dclient.controller.register_traffic([rule])

            with LydianClient(srchost) as sclient:
                sclient.controller.register_traffic([rule])


def get_podium():
    global _podium
    if not _podium:
        _podium = Podium()

    return _podium


def run_iperf3(src, dst, duration=10, udp=False, bandwidth=None,
               client_args='', server_args='', func_ip=None):
    """
    Run iperf between <src> and <dst> over TCP/UDP for <duration> seconds

    Returns iperf client output

    NOTE: By default the transfer rate is unlimited which consumes high CPU

    Parameters
    ----------
    src: host
        iperf client
    dst: host
        iperf server
    duration: int
        How long iperf should run
    udp: bool
        Whether to run in UDP mode or TCP (default: TCP)
    bandwidth: int
        Limit traffic to this many Mbits/second
    client_args: str
        Additional cli options supported by iperf client
    server_args: str
        Additional cli options supported by iperf server
    """
    _podium = get_podium()
    src_host = _podium.get_ep_host(src)
    dst_host = _podium.get_ep_host(dst)
    with LydianClient(dst_host) as server:
        with LydianClient(src_host) as client:
            try:
                port = server.iperf.start_iperf_server(args=server_args)
                log.info('iperf server: %s is running on port %s', dst_host, port)
                job_id = client.iperf.start_iperf_client(dst_host, port, duration, udp, bandwidth,
                                                         args=client_args)
                job_info = client.iperf.get_client_job_info(job_id)
                log.info('cmd: %s on iperf client running with job id: %d', job_info['cmd'],
                         job_id)
                time.sleep(duration)
                while job_info['state'] == 'running':
                    time.sleep(1)
                    job_info = client.iperf.get_client_job_info(job_id)
                    log.info('iperf client job: %d info %s', job_id, job_info)
                return job_info['result']
            finally:
                if port:
                    server.iperf.stop_iperf_server(port)
                    if job_id:
                        client.iperf.stop_iperf_client(job_id)


def start_pcap(host, pcap_file_name, interface, pcap_args='', func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.pcap.start_pcap(pcap_file_name, interface, pcap_args)


def stop_pcap(host, pcap_file_name, func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.pcap.stop_pcap(pcap_file_name)


def start_resource_monitoring(host, func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.monitor.start()


def stop_resource_monitoring(host, func_ip=None):
    """
    Starts packet capture on a requested host.
    """
    with LydianClient(_get_host_ip(host, func_ip)) as client:
        client.monitor.stop()
