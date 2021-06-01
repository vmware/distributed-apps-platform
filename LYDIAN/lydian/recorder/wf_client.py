#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import socket

import lydian.apps.config as conf
import lydian.common.core as core
import lydian.common.errors as errors

log = logging.getLogger(__name__)

try:
    from wavefront_sdk import WavefrontDirectClient, WavefrontProxyClient
except errors.ModuleNotFoundError:
    log.warn("Wavefront package is not installed. "
             "Recording to it would be disabled.")
    from lydian.utils.mock import WavefrontDirectClient, \
        WavefrontProxyClient

def _get_wf_proxy_send():
    """
    Returns Wavefront Proxy client.
    """
    host = conf.get_param('WAVEFRONT_PROXY_ADDRESS')
    if not host:
        return None

    metrics_port = conf.get_param('WAVEFRONT_PROXY_METRICS_PORT')
    distribution_port = conf.get_param('WAVEFRONT_PROXY_DISTRIBUTION_PORT')
    tracing_port = conf.get_param('WAVEFRONT_PROXY_TRACING_PORT')
    event_port = conf.get_param('WAVEFRONT_PROXY_EVENT_PORT')

    return WavefrontProxyClient(
        host=host,
        metrics_port=metrics_port,
        distribution_port=distribution_port,
        tracing_port=tracing_port)

def _get_wf_sender():
    """
    Returns Wavefront sender
    """
    # max queue size (in data points). Default: 50,000
    # batch size (in data points). Default: 10,000
    # flush interval  (in seconds). Default: 1 second

    # First try to get Wavefront Proxy client
    proxy = _get_wf_proxy_send()
    if proxy:
        return proxy

    server = conf.get_param('WAVEFRONT_SERVER_ADDRESS')
    token = conf.get_param('WAVEFRONT_SERVER_API_TOKEN')
    return WavefrontDirectClient(
        server=server, token=token) if server and token else None


class WavefrontRecorder(core.Subscribe):
    ENABLE_PARAM = 'WAVEFRONT_RECORDING'

    def __init__(self):
        super(WavefrontRecorder, self).__init__()
        self._client = _get_wf_sender()
        self._testbed = conf.get_param('TESTBED_NAME')
        self._testid = str(conf.get_param('TEST_ID'))
        self.node = socket.gethostname()

        if not self._client:
            # If client not instantiated properly, disable the recorder.
            log.info("Recording to Wavefront disabled due to invalid params.")
            self.set_config(self.ENABLE_PARAM, False)

    @property
    def enabled(self):
        return self.get_config(self.ENABLE_PARAM)

    def stop(self):
        if self._client:
            if isinstance(self._client, WavefrontDirectClient):
                self._client.flush_now()
            self._client.close()


class WavefrontTrafficRecorder(WavefrontRecorder):
    CONFIG_PARAMS = ['WAVEFRONT_TRAFFIC_RECORDING']
    ENABLE_PARAM = 'WAVEFRONT_TRAFFIC_RECORDING'

    @property
    def prefix(self):
        if conf.get_param('WAVEFRONT_USE_UNIQUE_METRIC'):
            return 'lydian.traffic.%s.%s.' % (self._testbed, self._testid)
        else:
            return 'lydian.traffic.'

    def write(self, record):
        if not self.enabled:
            return
        # assert isinstance(trec, TrafficRecord)
        prefix =  self.prefix + record.protocol
        tags = {
            "datacenter": self._testbed,
            "test_id": self._testid,
            "reqid": record.reqid,
            "ruleid": record.ruleid,
            "origin": record.source,
            "destination": record.destination,
            "node": self.node
            }

        source = conf.get_param('WAVEFRONT_SOURCE_TAG') or self._testbed

        # Record Traffic Data
        value = 1 if record.result else 0
        name = prefix + ".result"
        self._client.send_metric(
                    name=name, value=value,
                    timestamp=record.timestamp,
                    source=source,
                    tags=tags)

        # Record Latency data
        name = prefix + ".latency"
        self._client.send_metric(
                    name=name, value=record.latency,
                    timestamp=record.timestamp,
                    source=source,
                    tags=tags)


class WavefrontResourceRecorder(WavefrontRecorder):
    CONFIG_PARAMS = ['WAVEFRONT_RESOURCE_RECORDING']
    ENABLE_PARAM = 'WAVEFRONT_RESOURCE_RECORDING'

    @property
    def prefix(self):
        if conf.get_param('WAVEFRONT_USE_UNIQUE_METRIC'):
            return 'lydian.resources.%s.%s.' % (self._testbed, self._testid)
        else:
            return 'lydian.resources.'

    def write(self, record):
        if not self.enabled:
            return
        # assert isinstance(trec, ResourceRecord)
        prefix = self.prefix
        source = conf.get_param('WAVEFRONT_SOURCE_TAG') or self._testbed
        tags = {
            "datacenter": self._testbed,
            "node": self.node,
            "test_id": self._testid
            }
        for key, val in record.as_dict().items():
            if key in ['_id', '_timestamp']:
                continue
            metric = prefix + key
            self._client.send_metric(
                    name=metric, value=val,
                    timestamp=record.timestamp,
                    source=source,
                    tags=tags)
