#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
import itertools
import json
import logging
import pickle
import sys
import time

from lydian.apps import podium
from lydian.controller.client import LydianClient
from lydian.utils import logger

khosts = {}
dhosts = {}
uhosts = {}

def run_test(host_info):

    khosts = host_info["kali"]["hosts"]
    khost_user = host_info["kali"]["user"]
    khost_passwd = host_info["kali"]["password"]

    dhosts = host_info["dvwa"]["hosts"]
    dhost_user = host_info["dvwa"]["user"]
    dhost_passwd = host_info["dvwa"]["password"]

    uhosts = host_info["ubuntu"]["hosts"]
    uhost_user = host_info["ubuntu"]["user"]
    uhost_passwd = host_info["ubuntu"]["password"]

    pod = podium.get_podium()

    pod.cleanup_hosts(khosts, khost_user, khost_passwd)
    pod.cleanup_hosts(uhosts, uhost_user, uhost_passwd)
    pod.cleanup_hosts(dhosts, dhost_user, dhost_passwd)
    pod.add_hosts(khosts, khost_user, khost_passwd)
    pod.add_hosts(uhosts, uhost_user, uhost_passwd)
    pod.add_hosts(dhosts, dhost_user, dhost_passwd)

    # pod.start_api_server()
    targets = itertools.cycle(dhosts + uhosts)

    tasks = {}
    workers = {}
    for host in khosts:
        with LydianClient(host) as worker:
            target = next(targets)
            log.info("Starting run from host %s on target %s", host, target)
            reqid = worker.rapidscan.start_run(target)
            log.info("Request id is %s", reqid)
            tasks[host] = {"reqid": reqid, "target": target}

    DONE = False
    running_tasks = tasks
    all_results = []
    start = time.time()
    while running_tasks and time.time() - start <  1000:
        log.info("Time elapsed: %3.2f seconds", time.time() - start)
        rtasks = tasks
        for host, work in list(tasks.items()):
            target = work["target"]
            reqid = work["reqid"]
            with LydianClient(host) as worker:
                if worker.rapidscan.is_run_complete(reqid):
                    log.info("Checking scan data for host %s on target %s", host, target)
                    worker.rapidscan.save_results_to_db(reqid)
                    result = worker.rapidscan.get_result(reqid)
                    del running_tasks[host]
                    all_results.extend(result)
                else:
                    log.info("scan continuing for host %s on target %s", host, target)
        time.sleep(10)
    for res in all_results:
        log.info("host: %s tool: %s reqid: %s severity: %s message: %s", res[0], res[1], res[2], res[3], res[4])



if __name__ == "__main__":
    # TODO: Add arg parser support
    log = logger.setup_logging()
    if len(sys.argv) > 1:
        ip_file = sys.argv[1]
        with open(ip_file, "r") as fd:
            hosts = json.load(fd)
        run_test(hosts)
