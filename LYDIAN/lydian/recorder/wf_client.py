#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

from wavefront_sdk import WavefrontDirectClient

import lydian.apps.config as conf

def _get_wf_sender():
    # Create a sender with:
    # your Wavefront URL
    # a Wavefront API token that was created with direct ingestion permission
    # max queue size (in data points). Default: 50,000
    # batch size (in data points). Default: 10,000
    # flush interval  (in seconds). Default: 1 second
    return WavefrontDirectClient(
        server='https://vmware.wavefront.com',
        token='d9302bfa-89b4-4d7f-995e-830887b9e903')


class WavefrontRecorder(object):

    def __init__(self):
        self._client = _get_wf_sender()
        self._testbed = conf.TESTBED_NAME or ''
        self._testid = conf.TEST_ID or ''


class WavefrontTrafficRecorder(WavefrontRecorder):

    def write(self, record):
        # assert isinstance(trec, TrafficRecord)
        prefix = 'lydian.traffic.' + record.protocol + ".result"
        tags = {
            "datacenter": self._testbed,
            "test_id": self._testbed,
            "reqid": record.reqid,
            "ruleid": record.ruleid,
            "source": record.source,
            "destination": record.destination
            }
        value=1 if record.result else 0
        self._client.send_metric(
                    name=prefix, value=value,
                    timestamp=record.timestamp,
                    source=conf.WAVEFRONT_SOURCE_TAG,
                    tags=tags)


class WavefrontResourceRecorder(WavefrontRecorder):

    def write(self, record):
        # assert isinstance(trec, ResourceRecord)
        prefix = 'lydian.resources.'
        tags = {"datacenter": self._testbed,
                "test_id": self._testid}
        for key, val in record.as_dict().items():
            if key in ['_id', '_timestamp']:
                continue
            metric = prefix + key
            self._client.send_metric(
                    name=metric, value=val,
                    timestamp=record.timestamp,
                    source=conf.WAVEFRONT_SOURCE_TAG, tags=tags)
