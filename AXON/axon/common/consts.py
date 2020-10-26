#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import platform

SYSTEM = platform.system()
LINUX_OS = True if SYSTEM == 'Linux' else False
MAC_OS = True if SYSTEM == 'Darwin' else False
WIN_OS = True if SYSTEM == 'Windows' else False

# Logging Constants
LINUX_LOG_DIR = "/var/log/axon"
WIN_LOG_DIR = "C:\\axon\\log"
if LINUX_OS or MAC_OS:
    LOG_DIR = LINUX_LOG_DIR
elif WIN_OS:
    LOG_DIR = WIN_LOG_DIR
LOG_FILE = "axon.log"

# Axon Service Constants
AXON_PORT = 5678

# Recorder Constants
WAVEFRONT = 'wavefront'
SQL = 'sql'
ELASTIC_SEARCH = 'elasticsearch'
ELASTIC_SEARCH_PORT = 9200
