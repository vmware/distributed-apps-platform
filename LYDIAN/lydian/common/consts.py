#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
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

    NODE_PREP_MAX_THREAD = int(os.environ.get('NODE_PREP_MAX_THREAD', 32))
    LYDIAN_SERVICE_WAIT_TIME = int(os.environ.get('LYDIAN_SERVICE_WAIT_TIME', 4))
    # Wait for 5 seconds while joining the threads.
    THREADS_JOIN_TIMEOUT = 5

    # Default parallelism for common operations.
    DEFAULT_CONCURRENCY = 32


class LoggingConstants(Constants):
    _NAME = "Logging"
    LINUX_LOG_DIR = os.environ.get('LINUX_LOG_DIR', "/var/log/lydian")
    WIN_LOG_DIR = os.environ.get('WIN_LOG_DIR', "C:\\lydian\\log")
    LYDIAN_LOG_DIR = LINUX_LOG_DIR if LINUX_OS or MAC_OS else None
    LYDIAN_LOG_DIR = LYDIAN_LOG_DIR or (WIN_LOG_DIR if WIN_OS else "./")
    LYDIAN_LOG_FILE = "lydian.log"

    PARAMIKO_LOG_LEVEL = os.environ.get('PARAMIKO_LOG_LEVEL', 'ERROR')
    RPYC_LOG_LEVEL = os.environ.get('RPYC_LOG_LEVEL', 'INFO')


class LydianServiceConstants(Constants):
    _NAME = "Lydian Service"
    LYDIAN_PORT = int(os.environ.get('LYDIAN_PORT', 5649))
    LYDIAN_CONFIG = os.environ.get('LYDIAN_CONFIG', '/etc/lydian/lydian.conf')
    LYDIAN_EGG_PATH = os.environ.get('LYDIAN_EGG_PATH', '')
    LYDIAN_HOSTPREP_CONFIG = os.environ.get('LYDIAN_HOSTPREP_CONFIG', '')


class Sqlite3Constants(Constants):
    _NAME = "SQLITE3 Constants"
    SQLITE3_CONNECTION_TIMEOUT = int(os.environ.get('SQLITE3_CONNECTION_TIMEOUT', 20))


class TestbedConstants(Constants):
    _NAME = "Testbed"
    TEST_ID = os.environ.get('TEST_ID', '1234')
    TESTBED_NAME = os.environ.get('TESTBED_NAME', socket.gethostname())

    ENDPOINT_USERNAME = os.environ.get('ENDPOINT_USERNAME', 'root')
    ENDPOINT_PASSWORD = os.environ.get('ENDPOINT_PASSWORD', 'FAKE_PASSWORD')
    LYDIAN_NTP_SERVER = os.environ.get('LYDIAN_NTP_SERVER', None)   # e. g. ntp1.eng.vmware.com

    # Controls Egg generation / consumption for endpoints.
    # Pristine egg is generated from pypi server. Local egg is generated from
    # locally installed/modified code. Resue setting generates egg only if not
    # already present.
    LYDIAN_EGG_TYPE = os.environ.get('LYDIAN_EGG_TYPE', 'LOCAL')


class NamespaceConstants(Constants):
    _NAME = "Namespace"
    # Namespace Configs
    NAMESPACE_DIR = '/var/run/netns'
    NAMESPACE_INTERFACE_NAME_PREFIXES = ["veth", "eth", "vmk"]


class TrafficConstants(Constants):
    _NAME = "Traffic"
    # Traffic Configs

    TRAFFIC_START_SERVERS_FIRST = os.environ.get('TRAFFIC_START_SERVERS_FIRST', True)

    # Allows traffic queries to be backdated by these many seconds.
    # e.g. if someone says get reuslts for last 20 seconds, it will
    # backdate 20 seconds by 15 seconds. It's mainly done to allow
    # offsetting of clock synchronization issue (to some extent).
    TRAFFIC_STATS_QUERY_LATENCY = int(os.environ.get('TRAFFIC_STATS_QUERY_LATENCY', 15))


class RecorderConstants(Constants):
    _NAME = "Data Recording"
    WAVEFRONT_TRAFFIC_RECORDING = os.environ.get('WAVEFRONT_TRAFFIC_RECORDING',
                                                 True)
    WAVEFRONT_RESOURCE_RECORDING = os.environ.get('WAVEFRONT_RESOURCE_RECORDING',
                                                 True)
    ELASTICSEARCH_TRAFFIC_RECORDING = os.environ.get('ELASTICSEARCH_TRAFFIC_RECORDING',
                                                              True)

    # SQLITE recording configs
    SQLITE_TRAFFIC_RECORDING = os.environ.get('SQLITE_TRAFFIC_RECORDING', True)
    SQLITE_RESOURCE_RECORDING = os.environ.get('SQLITE_RESOURCE_RECORDING', True)

    RECORD_UPDATER_THREAD_POOL_SIZE = int(os.environ.get('RECORD_UPDATER_THREAD_POOL_SIZE', 2))
    RESOURCE_RECORD_REPORT_FREQ = int(os.environ.get('RESOURCE_RECORD_REPORT_FREQ', 4))
    TRAFFIC_RECORD_REPORT_FREQ = int(os.environ.get('TRAFFIC_RECORD_REPORT_FREQ', 4))


class WavefrontConstants(Constants):
    _NAME = "Wavefront"
    # Direct Client constants
    WAVEFRONT_SERVER_ADDRESS = os.environ.get('WAVEFRONT_SERVER_ADDRESS', '')
    WAVEFRONT_SERVER_API_TOKEN = os.environ.get('WAVEFRONT_SERVER_API_TOKEN', '')
    WAVEFRONT_SOURCE_TAG = os.environ.get('WAVEFRONT_SOURCE', '')

    # Wavefront Proxy client constants
    WAVEFRONT_PROXY_ADDRESS = os.environ.get('WAVEFRONT_PROXY_ADDRESS', '')
    WAVEFRONT_PROXY_METRICS_PORT = int(os.environ.get('WAVEFRONT_PROXY_METRICS_PORT', 2878))
    WAVEFRONT_PROXY_DISTRIBUTION_PORT = int(os.environ.get('WAVEFRONT_PROXY_DISTRIBUTION_PORT', 2878))
    WAVEFRONT_PROXY_TRACING_PORT = int(os.environ.get('WAVEFRONT_PROXY_TRACING_PORT', 30000))

    # Wavefront Query releated constants
    WAVEFRONT_USE_UNIQUE_METRIC = os.environ.get('WAVEFRONT_USE_UNIQUE_METRIC', False)


class ELSConstants(Constants):
    _NAME = "Elastic Search"
    ELASTIC_SEARCH_SERVER_ADDRESS = os.environ.get('ELASTIC_SEARCH_SERVER_ADDRESS', '')
    ELASTIC_SEARCH_SERVER_PORT = int(os.environ.get('ELASTIC_SEARCH_SERVER_PORT', 9200))
    ELASTIC_SEARCH_SERVER_INDEX = os.environ.get('ELASTIC_SEARCH_SERVER_INDEX', '')
    ELASTIC_SEARCH_SOURCE_TAG = os.environ.get('ELASTIC_SEARCH_SOURCE', '')
    LYDIAN_ES_NS_NAME = os.environ.get('LYDIAN_ES_NS_NAME', '')

def get_categories():
    """
    Returns list of all the constant categories.
    """
    return [
        SystemConstants,
        Sqlite3Constants,
        LoggingConstants,
        LydianServiceConstants,
        TestbedConstants,
        NamespaceConstants,
        TrafficConstants,
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
