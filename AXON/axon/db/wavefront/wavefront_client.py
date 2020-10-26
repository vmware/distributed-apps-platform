import datetime
import random

from wavefront_sdk import WavefrontDirectClient, WavefrontProxyClient
from wavefront_sdk.common import metric_to_line_data

from axon.common import config as conf

METRIC_PRIFIX = 'axon.traffic.'


class TrafficRecord(object):

    METRIC = METRIC_PRIFIX + 'traffic_record'

    def __init__(self, client, traffic_record):
        self._client = client
        self._traffic_record = traffic_record

    def save(self):
        if self.report_to_wavefront():
            tags = {"datacenter": conf.TESTBED_NAME,
                    "test_id": conf.TEST_ID}
            metric_suffix = '.success' if self._traffic_record.success else\
                '.failure'
            metric = self.METRIC + metric_suffix
            val = 1 if self._traffic_record.success else 0
            tags['src'] = self._traffic_record.src
            tags['dst'] = self._traffic_record.dst
            tags['port'] = str(self._traffic_record.port)
            tags['protocol'] = self._traffic_record.traffic_type
            tags['error'] = str(self._traffic_record.error)
            tags['connected'] = \
                'true' if self._traffic_record.connected else 'false'
            tags['created'] = datetime.datetime.fromtimestamp(
                self._traffic_record.created).strftime('%c')
            self._client.send_metric(
                name=metric, value=val,
                timestamp=self._traffic_record.created,
                source=tags['src'], tags=tags)

    def report_to_wavefront(self):
        return random.random() <= conf.WAVEFRONT_REPORT_PERC


class RecordCount(object):

    METRIC = METRIC_PRIFIX + 'request_count.'

    def __init__(self, client, proto_record_dict, created_time):
        self._client = client
        self._proto_record_dict = proto_record_dict
        self._created_time = created_time

    def save(self):
        batch_metric_data = []
        total_success = 0
        total_failure = 0
        tags = {"datacenter": conf.TESTBED_NAME,
                "test_id": conf.TEST_ID}
        for proto in self._proto_record_dict.keys():
            SUCCESS_METRIC = self.METRIC + proto.lower() + '.success'
            FAILURE_METRIC = self.METRIC + proto.lower() + '.failure'
            total_success += self._proto_record_dict[proto]['success']
            total_failure += self._proto_record_dict[proto]['failure']
            success_data = metric_to_line_data(
                name=SUCCESS_METRIC,
                value=self._proto_record_dict[proto]['success'],
                timestamp=self._created_time,
                source=conf.WAVEFRONT_SOURCE_TAG, tags=tags,
                default_source=conf.WAVEFRONT_SOURCE_TAG)
            failure_data = metric_to_line_data(
                name=FAILURE_METRIC,
                value=self._proto_record_dict[proto]['failure'],
                timestamp=self._created_time,
                source=conf.WAVEFRONT_SOURCE_TAG, tags=tags,
                default_source=conf.WAVEFRONT_SOURCE_TAG)
            batch_metric_data.extend([success_data, failure_data])
        success_metric = metric_to_line_data(
            name=self.METRIC + 'success',
            value=total_success, timestamp=self._created_time,
            source=conf.WAVEFRONT_SOURCE_TAG, tags=tags,
            default_source=conf.WAVEFRONT_SOURCE_TAG)
        failure_metric = metric_to_line_data(
            name=self.METRIC + 'failure',
            value=total_failure, timestamp=self._created_time,
            source=conf.WAVEFRONT_SOURCE_TAG, tags=tags,
            default_source=conf.WAVEFRONT_SOURCE_TAG)
        batch_metric_data.extend([success_metric, failure_metric])
        self._client.send_metric_now(batch_metric_data)


class LatencyStats(object):

    METRIC = METRIC_PRIFIX + 'avg_latency'

    def __init__(self, client, latency_sum, samples, created_time):
        self._client = client
        self._latency_sum = latency_sum
        self._samples = samples
        self._created_time = created_time

    def save(self):
        avg_latency = 0 if not self._samples else \
            self._latency_sum / self._samples
        tags = {"datacenter": conf.TESTBED_NAME,
                "test_id": conf.TEST_ID}
        self._client.send_metric(
            name=self.METRIC, value=avg_latency,
            timestamp=self._created_time,
            source=conf.WAVEFRONT_SOURCE_TAG, tags=tags)


class WavefrontClient(object):
    def __init__(self, server, proxy=False, token=None):
        if not proxy:
            self._client = WavefrontDirectClient(server, token)
        else:
            self._client = WavefrontProxyClient(
                host=server, metrics_port=2878,
                distribution_port=2878, tracing_port=30000)

    def create_record_count(self, proto_record_dict, created):
        record_count = RecordCount(self._client, proto_record_dict, created)
        record_count.save()

    def create_traffic_record(self, traffic_record):
        record = TrafficRecord(self._client, traffic_record)
        record.save()

    def create_resource_record(self, record):
        prefix = 'axon.resources.'
        tags = {"datacenter": conf.TESTBED_NAME,
                "test_id": conf.TEST_ID}
        for key, val in record.as_dict().items():
            if key in ['_id', '_timestamp']:
                continue
            metric = prefix + key
            self._client.send_metric(
                    name=metric, value=val,
                    timestamp=record.timestamp,
                    source=conf.WAVEFRONT_SOURCE_TAG, tags=tags)

    def create_latency_stats(self, latency_sum, samples, created):
        latency_stats = LatencyStats(
            self._client, latency_sum, samples, created)
        latency_stats.save()
