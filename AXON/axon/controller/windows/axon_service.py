#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import logging
import sys

from axon.controller.axon_rpyc_controller import AxonController


class AxonService(win32serviceutil.ServiceFramework):
    """
    Axon windows service class
    This is windows service class intended to work only for windows
    operating system.
    This uses pywin32 python library to interact with windows APIs.
    This utilises example service structure of ServiceFramework from
    win32serviceutil.

    Prerequisite: pywin32 library must be installed.
    """
    _svc_name_ = "AxonWinService"
    _svc_display_name_ = "Axon Windows Service"

    def __init__(self, args):
        self.log = logging.getLogger(__name__)
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.axon_controller = AxonController()

    def SvcStop(self):
        """
        Stop the axon windows service.
        :return: None
        """
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        """
        Start Axon windows service.
        :return: None
        """
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def stop(self):
        """
        Prerequisite for Axon service stop.
        :return: None
        """
        self.axon_controller.stop()

    def main(self):
        """
        Actual Axon service body.
        This is basically rpyc controller method to start the service
        on default port.
        :return: None
        """
        self.axon_controller.start()


def main():
    """
    Main method to install/start/stop/update/remove Axon service.
    :return: None
    """
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AxonService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AxonService)


if __name__ == '__main__':
    main()
