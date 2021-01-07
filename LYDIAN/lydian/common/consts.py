#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
Default config and Common constants for Lydian application.
NOTE: This module shouldn't have dependency on any other internal
module.
'''
import os
import platform
import socket


class Constants(object):
    _NAME = ''


# CONSTANTS
SYSTEM = platform.system()
LINUX_OS = True if SYSTEM == 'Linux' else False
MAC_OS = True if SYSTEM == 'Darwin' else False
WIN_OS = True if SYSTEM == 'Windows' else False


#### CONSTANTS ####
class SystemConstants(Constants):
    _NAME = "System"
    SYSTEM = SYSTEM     # Platform value.
    LINUX_OS = LINUX_OS # True if running on Linux oS
    MAC_OS = MAC_OS     # True if running on MAC OS
    WIN_OS = WIN_OS     # True if running on Windows

    # Wait for 5 seconds while joining the threads.
    THREADS_JOIN_TIMEOUT = 5

class LoggingConstants(Constants):
    _NAME = "Logging"
    LINUX_LOG_DIR = os.environ.get('LINUX_LOG_DIR', "/var/log/lydian")
    WIN_LOG_DIR = os.environ.get('WIN_LOG_DIR', "C:\\lydian\\log")
    LOG_DIR = LINUX_LOG_DIR if LINUX_OS or MAC_OS else None
    LOG_DIR = LOG_DIR or (WIN_LOG_DIR if WIN_OS else "./")
    LOG_FILE = "lydian.log"


class LydianServiceConstants(Constants):
    _NAME = "Lydian Service"
    LYDIAN_PORT = int(os.environ.get('LYDIAN_PORT', 5649))
    LYDIAN_CONFIG = os.environ.get('LYDIAN_CONFIG', '/etc/lydian/lydian.conf')
    LYDIAN_EGG_PATH = os.environ.get('LYDIAN_EGG_PATH', '')
    LYDIAN_HOSTPREP_CONFIG = os.environ.get('LYDIAN_HOSTPREP_CONFIG', '')


class TestbedConstants(Constants):
    _NAME = "Testbed"
    TEST_ID = os.environ.get('TEST_ID', '1234')
    TESTBED_NAME = os.environ.get('TESTBED_NAME', socket.gethostname())


class NamespaceConstants(Constants):
    _NAME = "Namespace"
    # Namespace Configs
    NAMESPACE_DIR = '/var/run/netns'
    NAMESPACE_INTERFACE_NAME_PREFIXES = ["veth", "eth"]


class RecorderConstants(Constants):
    _NAME = "Data Recording"
    WAVEFRONT_TRAFFIC_RECORDING = os.environ.get('WAVEFRONT_TRAFFIC_RECORDING',
                                                 True)
    WAVEFRONT_RESOURCE_RECORDING = os.environ.get('WAVEFRONT_RESOURCE_RECORDING',
                                                 True)
    # SQLITE recording configs
    SQLITE_TRAFFIC_RECORDING = os.environ.get('SQLITE_TRAFFIC_RECORDING', True)
    SQLITE_RESOURCE_RECORDING = os.environ.get('SQLITE_RESOURCE_RECORDING', True)

    RECORD_UPDATER_THREAD_POOL_SIZE = int(os.environ.get('RECORD_UPDATER_THREAD_POOL_SIZE', 2))
    RESOURCE_RECORD_REPORT_FREQ = int(os.environ.get('RESOURCE_RECORD_REPORT_FREQ', 4))
    TRAFFIC_RECORD_REPORT_FREQ = int(os.environ.get('TRAFFIC_RECORD_REPORT_FREQ', 4))


class WavefrontConstants(Constants):
    _NAME = "Wavefront"
    WAVEFRONT_SERVER_ADDRESS = os.environ.get('WAVEFRONT_SERVER_ADDRESS', '')
    WAVEFRONT_SERVER_API_TOKEN = os.environ.get('WAVEFRONT_SERVER_API_TOKEN', '')
    WAVEFRONT_SOURCE_TAG = os.environ.get('WAVEFRONT_SOURCE', socket.gethostname())
    WAVEFRONT_PROXY_ADDRESS = os.environ.get('WAVEFRONT_PROXY_ADDRESS', '')
    WAVEFRONT_PROXY_METRICS_PORT = int(os.environ.get('WAVEFRONT_PROXY_METRICS_PORT', 2878))
    WAVEFRONT_PROXY_DISTRIBUTION_PORT = int(os.environ.get('WAVEFRONT_PROXY_DISTRIBUTION_PORT', 2878))
    WAVEFRONT_PROXY_TRACING_PORT = int(os.environ.get('WAVEFRONT_PROXY_TRACING_PORT', 30000))


class ELSConstants(Constants):
    _NAME = "Elastic Search"
    ELASTIC_SEARCH_SERVER_ADDRESS = os.environ.get('ELASTIC_SEARCH_SERVER_ADDRESS', '')
    ELASTIC_SEARCH_SERVER_PORT = int(os.environ.get('ELASTIC_SEARCH_SERVER_PORT', 9200))


def get_categories():
    """
    Returns list of all the constant categories.
    """
    return [
        SystemConstants,
        LoggingConstants,
        LydianServiceConstants,
        TestbedConstants,
        NamespaceConstants,
        RecorderConstants,
        WavefrontConstants,
        ELSConstants
    ]

def get_constants(categories=None):
    """
    Returns constants under the 'categories'. If not list is provided,
    returns all the constants with default values.
    """
    _categories = categories or get_categories()
    _constants = {}
    for category in _categories:
        for key, val in category.__dict__.items():
            if key.startswith('_') or not key.isupper():
                continue
            _constants[key] = val

    return _constants
