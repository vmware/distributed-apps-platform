#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import os
import queue
import threading

from lydian.apps import config as config
from lydian.traffic.core import TrafficRecord
from lydian.traffic.client import TCPClient, UDPClient, HTTPClient
from lydian.traffic.server import TCPServer, UDPServer, HTTPServer
from lydian.utils.nsenter import Namespace


log = logging.getLogger(__name__)


class TrafficTask(object):

    CLIENT = 'CLIENT'
    SERVER = 'SERVER'
    LINUX_NS_DIR = '/var/run/netns/'

    def __init__(self, trule):
        self._task = None
        self._type = None
        self._trule = trule   # Traffic Rule
        self._task_thread = None
        self._ns_task_iter = None   # used only in NS Tasks
        self._create_task()

    def is_client(self):
        return self._type == self.CLIENT

    def is_server(self):
        return self._type == self.SERVER

    @property
    def target(self):
        return None

    @property
    def traffic_rule(self):
        return self._trule

    def _create_task(self):
        if self.target.is_vmhost():
            self._create_vmhost_task()
        elif self.target.is_namespace():
            self._create_namspace_task()
        elif self.target.is_container():
            self._create_container_task()
        else:
            log.error("Unknown target for rule : %s",
                      self._trule)

    def _create_vmhost_task(self):
        raise NotImplementedError("_create_vmhost_task")

    def _create_namspace_task(self):
        raise NotImplementedError("_create_namspace_task")

    def _create_container_task(self):
        raise NotImplementedError("_create_container_task")

    def _ns_task_helper(self, ns_name, func):
        with Namespace(os.path.join(self.LINUX_NS_DIR,ns_name), 'net'):
            yield func()

    def start(self, blocking=False):
        if blocking:
            self._task.start()
        else:
            self._task_thread = threading.Thread(target=self._task.start,
                                                 daemon=True)
            self._task_thread.start()

    def _join_thread(self):
        if self._task_thread:
            self._task_thread.join(config.get_param('THREADS_JOIN_TIMEOUT'))
            self._task_thread = None

    def stop(self):
        self._task.stop()
        self._join_thread()

    def close(self):
        self._task.close()
        self._join_thread()
        if self._ns_task_iter:
            # release resources.
            try:
                next(self._ns_task_iter)
            except StopIteration:
                pass    # expected.
            self._ns_task_iter = None

    def is_running(self):
        return not self._task.stopped()


class TrafficClientTask(TrafficTask):

    def __init__(self, record_queue, trule):
        self._record_queue = record_queue
        self._type = self.CLIENT
        super(TrafficClientTask, self).__init__(trule)

    @property
    def target(self):
        return self._trule.src_target

    @property
    def record_queue(self):
        return self._record_queue

    def _get_client(self):
        kwargs = {}
        kwargs['server'] = self.traffic_rule.dst
        kwargs['port'] = self.traffic_rule.port
        kwargs['handler'] = self.ping_handler

        kwargs['payload'] = getattr(self.traffic_rule, 'payload', None)
        kwargs['tries'] = getattr(self.traffic_rule, 'tries', None)
        kwargs['sockettimeout'] = getattr(self.traffic_rule, 'sockettimeout',
                                          None)
        frequency = getattr(self.traffic_rule, 'frequency', None)
        if frequency:
            kwargs['frequency'] = frequency
        kwargs['interval'] = getattr(self.traffic_rule, 'interval', None)
        kwargs['verbose'] = getattr(self.traffic_rule, 'verbose', None)

        if self.traffic_rule.is_TCP():
            return TCPClient(**kwargs)
        elif self.traffic_rule.is_UDP():
            return UDPClient(**kwargs)
        elif self.traffic_rule.is_HTTP():
            return HTTPClient(**kwargs)
        else:
            msg = "LYDIAN: Unsupported protocol on rule %s" % self._trule
            raise NotImplementedError(msg)

    def _create_vmhost_task(self):
        self._task = self._get_client()

    def _create_namspace_task(self):
        self._ns_task_iter = self._ns_task_helper(self.target.name,
                                                  self._get_client)
        self._task = next(self._ns_task_iter)

    def ping_handler(self, payload, data, latency):
        try:
            rec = TrafficRecord()
            rec.source = self._trule.src
            rec.destination = self._trule.dst
            rec.protocol = self._trule.protocol
            rec.port = self._trule.port
            rec.expected = self._trule.connected in [1, '1']
            rec.result = not rec.expected ^ (data == payload)
            rec.reqid = self._trule.reqid
            rec.ruleid = self._trule.ruleid
            rec.latency = latency
            # log.info("Traffic: %r", rec)
            self.record_queue.put(rec, block=False, timeout=2)
        except queue.Full as err:
            log.error("Cann't put Traffic Record %r into the queue: %r",
                      rec, err)


class TrafficServerTask(TrafficTask):

    def __init__(self, trule):
        self._type = self.SERVER
        super(TrafficServerTask, self).__init__(trule)

    @property
    def target(self):
        return self._trule.dst_target

    def _get_server(self):
        port = self._trule.port
        if self._trule.is_TCP():
            return TCPServer(port=port)
        elif self._trule.is_UDP():
            return UDPServer(port=port)
        elif self._trule.is_HTTP():
            return HTTPServer(port=port)
        else:
            msg = "LYDIAN: Unsupported protocol on rule %s" % self._trule
            raise NotImplementedError(msg)

    def _create_vmhost_task(self):
        self._task = self._get_server()

    def _create_namspace_task(self):
        self._ns_task_iter = self._ns_task_helper(self.target.name,
                                                  self._get_server)
        self._task = next(self._ns_task_iter)
