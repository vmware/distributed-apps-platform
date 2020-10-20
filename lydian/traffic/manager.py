#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging

import lydian.traffic.core as core
import lydian.traffic.task as task

log = logging.getLogger(__name__)


class TrafficManager(object):
    TASK_TYPE = None

    def __init__(self):
        self._traffic_tasks = {}

    def key(self, trule):
        raise NotImplementedError("'key' method must be implemented.")

    def _create_task(self, trule):
        raise NotImplementedError("'key' method must be implemented.")

    def add_task(self, trule):
        """
        Relationship { Traffic Client : Traffic Rule } is 1:1.
        """
        key = self.key(trule)
        assert key, "Invalid ruleid"
        if key in self._traffic_tasks:
            log.error("Traffic task (%s) already running for ruleid: %s",
                      self.TASK_TYPE, trule.ruleid)
            return

        task = self._create_task(trule)
        if trule.enabled:
            task.start()    # Start the task if enabled.
        self._traffic_tasks[key] = task

    def start(self, trule):
        """ Start a Traffic task (again). """
        key = self.key(trule)
        if key in self._traffic_tasks:
            self._traffic_tasks[key].start()

    def stop(self, trule):
        """ Stop a Traffic task. """
        key = self.key(trule)
        if key in self._traffic_tasks:
            self._traffic_tasks[key].stop()

    def close(self):
        for _, task in self._traffic_tasks.items():
            task.close()
        self._traffic_tasks = {}

    def num_tasks(self):
        return len(self._traffic_tasks)


class ClientManager(TrafficManager):
    """
    Manages Traffic Client on a host/vm.
    """
    TASK_TYPE = task.TrafficTask.CLIENT

    def __init__(self, record_queue):
        self._record_queue = record_queue
        super(ClientManager, self).__init__()

    def key(self, trule):
        # A client can be uniquely identified with the rule it is
        # attached to. Two clients can be alike except for the
        # ruleid they are attached to.
        return trule.ruleid

    def _create_task(self, trule):
        return task.TrafficClientTask(self._record_queue, trule)


class ServerManager(TrafficManager):
    """
    Manages Traffic Client on a host/vm.
    Relationship { Traffic Server : Traffic Rule } is 1:N. Basically,
    there can be multiple Traffic Rules requiring to start same server
    and that would be a valid request.
    """
    TASK_TYPE = task.TrafficTask.SERVER

    def key(self, trule):
        # A server can be uniquely identified by its target host,
        # protocol and port associated.
        return (trule.dst_target.name, trule.protocol, trule.port)

    def _create_task(self, trule):
        return task.TrafficServerTask(trule)
