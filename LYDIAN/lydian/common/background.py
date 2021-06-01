#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

"""
Implements the background job mixin.
"""
import logging
import threading

log = logging.getLogger(__name__)


class BackgroundMixin(object):

    def __init__(self):
        self._stop_switch = threading.Event()
        self._task_name = ''
        self._task_thread = None
        self._run = None
        self._stop_switch.set()  # Stopped until started.

    @property
    def stopped(self):
        return self._stop_switch.isSet()

    def on(self):
        if not self.stopped:
            log.warn('Task, %s, is already running.', self._task_name)
            return False

        self._stop_switch.clear()
        self._task_thread = threading.Thread(target=self._run, daemon=True)
        self._task_thread.start()
        return True

    def off(self):
        if self.stopped:
            log.warn('Task, %s, is already stopped.', self._task_name)
            return False

        self._stop_switch.set()
        self._task_thread.join()
        self._task_thread = None
        return True
