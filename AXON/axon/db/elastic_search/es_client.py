import datetime
import logging
import time
import uuid

from axon.common import config as conf

from elasticsearch import Elasticsearch


class ElasticSearchClient(object):
    log = logging.getLogger(__name__)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)

    def __init__(self, host, port):
        if host is None or port is None:
            raise ValueError("Elasticsearch host or port can not be none")
        self._client = Elasticsearch(host=host, port=int(port))
        self._index = 'axon'

    def send(self, body):
        try:
            self._client.index(
                index=self._index, id=str(uuid.uuid4()), body=body)
        except Exception as e:
            self.log.error(
                "Failed to send data to elasticsearch due to %s" % e)

    def create_record_count(self, proto_record_dict, created):
        for proto in proto_record_dict.keys():
            body = {"datacenter": conf.TESTBED_NAME,
                    "test_id": conf.TEST_ID,
                    "type": "summary"}
            body.update({'success': proto_record_dict[proto]['success'],
                         'failure': proto_record_dict[proto]['failure'],
                         'created': created,
                         'source': conf.WAVEFRONT_SOURCE_TAG,
                         'timestamp': time.time()})
            self.send(body)

    def create_traffic_record(self, traffic_record):
        body = {"datacenter": conf.TESTBED_NAME,
                "test_id": conf.TEST_ID, "type": "record",
                'timestamp': time.time()}
        body['src'] = traffic_record.src
        body['dst'] = traffic_record.dst
        body['port'] = traffic_record.port
        body['protocol'] = traffic_record.traffic_type
        body['error'] = str(traffic_record.error)
        body['connected'] = \
            'true' if traffic_record.connected else 'false'
        body['created'] = traffic_record.created
        body['source'] = conf.WAVEFRONT_SOURCE_TAG
        body['result'] = 1 if traffic_record.success else 0
        self.send(body)

    def create_latency_stats(self, latency_sum, samples, created):
        body = {"datacenter": conf.TESTBED_NAME,
                "test_id": conf.TEST_ID, "type": "latency",
                'timestamp': time.time()}
        body["result"]  = 0 if not samples else (latency_sum / samples)
        body['source'] = conf.WAVEFRONT_SOURCE_TAG
        self.send(body)