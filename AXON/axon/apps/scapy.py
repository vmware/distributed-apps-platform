#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
- App for executing scapy code at remote endpoints.
"""
import logging

from scapy.all import *

# TODO : following adds the dependency on mock module.
# from scapy.utils import ContextManagerCaptureOutput

from axon.apps.base import BaseApp

log = logging.getLogger(__name__)


class Exec(BaseApp):

    def execute(self, code):
        # TODO : Delete this before we merge it upstream. 
        # It can be a potential security vulnerability.
        return exec(code)


class Scapy(Exec):

    NAME = 'ScapyApp'

    # In future, Scapy app shall provide more specific utility
    # functions for executing via RPyC but as of now, a very
    # basic and generic implementation simply executes the
    # python code passed as input to the call.

    def get_console(self, params):
        """
        Returns a session for console with given parameters.
        """
        pass

    def close_session(self, session_id=None):
        """
        Closes session with given id
        """
        pass
