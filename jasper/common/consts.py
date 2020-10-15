#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
Common constants for Lydian application.
'''
import os
import platform


LYDIAN_PORT = 5649

NAMESPACE_INTERFACE_NAME_PREFIXES = ["veth", "eth"]

#### CONSTANTS ####
SYSTEM = platform.system()
LINUX_OS = True if SYSTEM == 'Linux' else False
MAC_OS = True if SYSTEM == 'Darwin' else False
WIN_OS = True if SYSTEM == 'Windows' else False

# Logging Constants
LINUX_LOG_DIR = os.environ.get('LINUX_LOG_DIR', "/var/log/lydian")
WIN_LOG_DIR = os.environ.get('WIN_LOG_DIR', "C:\\lydian\\log")
if LINUX_OS or MAC_OS:
    LOG_DIR = LINUX_LOG_DIR
elif WIN_OS:
    LOG_DIR = WIN_LOG_DIR
LOG_FILE = "lydian.log"
