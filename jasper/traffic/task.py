#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging

from jasper.traffic.client import TCPClient, UDPClient
from jasper.traffic.server import TCPServer, UDPServer


log = logging.getLogger(__name__)


class TrafficTask(object):

    CLIENT = 'CLIENT'
    SERVER = 'SERVER'

    def __init__(self, trule):
        self._task = None
        self._type = None
        self._trule = trule   # Traffic Rule
        self._create_task()

    def is_client(self):
        return self._type == self.CLIENT

    def is_server(self):
        return self._type == self.SERVER

    @property
    def target(self):
        return None

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

    def start(self):
        self._task.start()

    def stop(self):
        self._task.stop()

    def close(self):
        self._task.close()

    def is_running(self):
        return not self._task.stopped()


class TrafficClientTask(TrafficTask):

    def __init__(self, trule):
        self._type = self.CLIENT
        super(TrafficClientTask, self).__init__(trule)

    @property
    def target(self):
        return self._trule.src_target

    def _get_client(self):
        server = self._trule.dst
        port = self._trule.port

        if self._trule.is_TCP():
            return TCPClient(server=server, port=port)
        elif self._trule.is_UDP():
            return UDPClient(server=server, port=port)
        else:
            msg = "Jasper: Unsupported protocol on rule %s" % self._trule
            raise NotImplementedError(msg)

    def _create_vmhost_task(self):
        self._task = self._get_client()


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
        else:
            msg = "Jasper: Unsupported protocol on rule %s" % self._trule
            raise NotImplementedError(msg)

    def _create_vmhost_task(self):
        self._task = self._get_server()
