#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import threading


class Connection(object):

    # Default server parameters
    MAX_CONNS = 20
    DEFAULT_TCP_SERVER_PORT = 5649
    DEFAULT_UDP_SERVER_PORT = 5648

    # Default client parameters
    TCP_CLIENT_PAYLOAD = "Dunkirk!!"

    # We are writing only a connection validation utility.
    # For our purpose, 50 bytes is good enough as payload
    # data.
    MAX_PAYLOAD_SIZE = 4096

    def __init__(self, verbose=False):
        self.log = logging.getLogger(__name__)
        self.verbose = verbose
        self._stop_event = threading.Event()
        self._stop_event.set()      # stopped until started
        self.socket = None

    def _create_socket(self):
        raise NotImplementedError("%s::_create_socket not implemented." % type(self).name)

    def stop(self):
        self._stop_event.set()

    def is_event_set(self):
        return self._stop_event.is_set()

    def clear_event(self):
        self._stop_event.clear()

    def set_event(self):
        self._stop_event.set()

    def start(self):
        raise NotImplementedError("%s::start not implemented" % type(self).name)

    def socket_close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def close(self):
        self.stop()
        self.socket_close()


    stopped = is_event_set
