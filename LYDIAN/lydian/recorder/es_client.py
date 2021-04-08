import datetime
import logging
import time
import uuid

import lydian.apps.config as conf
import lydian.common.core as core

log = logging.getLogger(__name__)
logging.getLogger('elasticsearch').setLevel(logging.WARNING)

try:
    from elasticsearch import Elasticsearch
except errors.ModuleNotFoundError:
    log.warn("Elasticsearch package is not installed."
             "Recording to it would be disabled.")
    from lydian.utils.mock import Elasticsearch

def _get_es_sender():
        host = conf.get_param('ELASTIC_SEARCH_SERVER_ADDRESS')
        port = conf.get_param('ELASTIC_SEARCH_SERVER_PORT')
        if host is None or port is None:
            raise ValueError("Elasticsearch host or port can not be none")
        client = Elasticsearch(host=host, port=int(port))
        return client


class ElasticSearchRecorder(core.Subscribe):
    ENABLE_PARAM = 'ELASTICSEARCH_RECORDING'

    def __init__(self):
        super(ElasticSearchRecorder, self).__init__()
        self._client = _get_es_sender()
        self._index = conf.get_param('ELASTIC_SEARCH_SERVER_INDEX')
        self._testbed = conf.get_param('TESTBED_NAME')
        self._testid = str(conf.get_param('TEST_ID'))

    @property
    def enabled(self):
        return self.get_config(self.ENABLE_PARAM)

    def stop(self):
        if self._client:
            self._client.transport.close()


class ElasticSearchTrafficRecorder(ElasticSearchRecorder):
    CONFIG_PARAMS = ['ELASTICSEARCH_TRAFFIC_RECORDING']
    ENABLE_PARAM = 'ELASTICSEARCH_TRAFFIC_RECORDING'

    def send(self, body):
        try:
            self._client.index(
                index=self._index, id=str(uuid.uuid4()), body=body)
        except Exception as e:
            self.log.error(
                "Failed to send data to elasticsearch due to %s" % e)

    def write(self, traffic_record):
        if not self.enabled:
            return
        body = {"datacenter": self._testbed,
                "test_id": self._testid, "type": "record",
                'timestamp': time.time()}
        body['origin'] = traffic_record.source
        body['destination'] = traffic_record.destination
        body['port'] = traffic_record.port
        body['protocol'] = traffic_record.protocol
        body['connected'] = \
            'true' if traffic_record.expected else 'false'
        body['created'] = traffic_record.timestamp
        body['source'] = conf.get_param('ELASTIC_SEARCH_SOURCE_TAG') or self._testbed
        body['ns_name'] =  conf.get_param('LYDIAN_ES_NS_NAME')
        body['result'] = 1 if traffic_record.result else 0
        self.send(body)

        body1 = {"datacenter": self._testbed,
                "test_id": self._testid, "type": "latency",
                'timestamp': time.time()}
        body1['origin'] = traffic_record.source
        body1['destination'] = traffic_record.destination
        body1['port'] = traffic_record.port
        body1['protocol'] = traffic_record.protocol
        body1['connected'] = \
             'true' if traffic_record.expected else 'false'
        body1['created'] = traffic_record.timestamp
        body1['result']  = traffic_record.latency
        body1['ns_name'] =  conf.get_param('LYDIAN_ES_NS_NAME')
        body1['source'] = conf.get_param('ELASTIC_SEARCH_SOURCE_TAG') or self._testbed
        self.send(body1)
