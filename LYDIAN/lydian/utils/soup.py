#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
Some general purpose recipes for common operations.
"""
import logging
import time

from lydian.utils.parallel import ThreadPool
from lydian.utils.ssh_host import Host


log = logging.getLogger(__name__)


def reboot_vms(hosts, username='root', password='FAKE_PASSWORD',
               worker_count=32):
    """
    Reboots VMs.
    """

    def _reboot_helper(hostip, username, password):
        try:
            with Host(host=hostip, user=username, passwd=password) as host:
                host.req_call('/sbin/reboot &')
        except Exception as err:
            log.error("Error in rebooting VM %s - erorr - %r ", hostip, err)

    params = [(host, (host, username, password), {}) for host in hosts]
    ThreadPool(_reboot_helper, params, workers=worker_count)


def _is_host_available(hostip, username, password, check_service=False):
    try:
        with Host(host=hostip, user=username, passwd=password) as host:
            host.req_call('ls -lrt /root')

        if check_service:
            with LydianClient(hostip) as lc:
                pass
        return True
    except Exception as _:
        return False


def get_avail_hosts(hosts, username='root', password='FAKE_PASSWORD',
                    check_service=False, worker_count=32, ):
    """
    Returns a tuple of list of reachable and unreachable node.
    A node is decided as reachable if we can SSH to it and also connect
    to it's Lydian service.
    """

    stime = time.time()

    params = [(host, (host, username, password, check_service), {}) for host in hosts]
    results = ThreadPool(_is_host_available, params, workers=worker_count)

    avails, fails = [], []
    for host, result in results.items():
        if result:
            avails.append(host)
        else:
            fails.append(host)

    etime = time.time()
    log.info("Took %s seconds to check availability on %s hosts",
              int(etime - stime), len(hosts))
    return avails, fails
