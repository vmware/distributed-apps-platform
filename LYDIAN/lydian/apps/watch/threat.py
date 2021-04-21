#!/usr/bin/env python
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import collections
import logging
import os
import time
import uuid

from lydian.apps.base import exposify
from lydian.apps.console import Console
from lydian.apps.internal.setup import SetupDB
from lydian.common.background import BackgroundMixin
from lydian.utils.common import get_host_name


log = logging.getLogger(__name__)


@exposify
class ThreatMonitor(Console, BackgroundMixin):
    NAME = "ThreatMonitor"
    INTERVAL = 4

    def __init__(self):
        Console.__init__(self)
        BackgroundMixin.__init__(self)
        
        self._run = self.run
        self.hostname = get_host_name()
        self.sudoers = set(self.get_sudoers())

        self.on()   # Turn on at start.

    def is_running(self):
        """
        Tells if app is available.
        """
        return True

    def get_sudoers(self):
        try:
            status, result = self.run_command("grep -Po '^sudo.+:\\K.*$' /etc/group")
            if not status:
                return result.split(',')
        except Exception as err:
            _ = err     # logging can bring VM down when run for long.

        return []

    def run(self):
        while not self.stopped:
            try:
                alerts = []
                sudoers = self.get_sudoers()
                for user in sudoers:
                    if user not in self.sudoers:
                        alerts.append("Privilege escalation for user %s" % user)
                
                with SetupDB() as db:
                    db.table = db.THREATS
                    for alert in alerts:
                        db.write(timestamp=time.time(),
                                 host=self.hostname,
                                 severity="HIGH",
                                 message=alert)
            except Exception as err:
                # log.error("Error in getting list of suoders.")
                _ = err     # ignore to avoid making log blob.
            finally:
                time.sleep(self.INTERVAL)

    def start(self):
        log.info("Starting Threat monitor ...")
        self.on()

    def stop(self):
        log.info("Starting Threat monitor ...")
        self.off()
