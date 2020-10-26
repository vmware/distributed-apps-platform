from collections import defaultdict
import logging
from threading import Thread
import time

from axon.common import config as conf
from axon.db.sql.analytics import session_scope
from axon.db.sql.repository import Repositories


class RecordCountHandler(Thread):

    log = logging.getLogger(__name__)

    def __init__(self, record_queue):
        super(RecordCountHandler, self).__init__()
        self.daemon = True
        self._record_queue = record_queue
        self._proto_record_count = defaultdict(
            lambda: {'success': 0, 'failure': 0})
        self._latency_sum = 0
        self._samples = 0
        self._last_updated_time = time.time()

    def _create_record_count(self, *args, **kwargs):
        raise NotImplementedError()

    def _create_latency_stats(self, *args, **kwargs):
        raise NotImplementedError()

    def run(self):
        self.log.info("Starting Record/Latency Count updater thread")
        while True:
            try:
                t_record = self._record_queue.get()
                self.update_counters(t_record)
            except Exception:
                self.log.exception("Exception happened during listening queue")

    def update_counters(self, t_record):
        if t_record.success:
            self._proto_record_count[t_record.traffic_type]['success'] += 1
            self._latency_sum += t_record.latency
            self._samples += 1
        else:
            self._proto_record_count[t_record.traffic_type]['failure'] += 1
        if time.time() - self._last_updated_time >= \
                conf.RECORD_COUNT_UPDATER_SLEEP_INTERVAL:
            self._create_record_count()
            self._create_latency_stats()
            self._last_updated_time = time.time()


class SqlRecordCountHandler(RecordCountHandler):

    def __init__(self, queue):
        super(SqlRecordCountHandler, self).__init__(queue)
        self._repositery = Repositories()

    def _create_record_count(self):
        created = time.time()
        for proto in list(self._proto_record_count.keys()):
            success_count = self._proto_record_count[proto]['success']
            failure_count = self._proto_record_count[proto]['failure']
            if success_count > 0 or failure_count > 0:
                with session_scope() as _session:
                    self._repositery.create_record_count(
                        _session, proto, success_count, failure_count, created)
                self._proto_record_count[proto]['success'] = 0
                self._proto_record_count[proto]['failure'] = 0

    def _create_latency_stats(self):
        created = time.time()
        with session_scope() as _session:
            self._repositery.create_latency_stats(
                _session, self._latency_sum, self._samples, created)
        self._latency_sum = 0
        self._samples = 0


class WavefrontRecordCountHandler(RecordCountHandler):
    def __init__(self, queue, wf_client):
        super(WavefrontRecordCountHandler, self).__init__(queue)
        self._wf_client = wf_client

    def _create_record_count(self):
        created = time.time()
        self._wf_client.create_record_count(self._proto_record_count, created)
        self._proto_record_count = defaultdict(
            lambda: {'success': 0, 'failure': 0})

    def _create_latency_stats(self):
        created = time.time()
        if self._samples > 0:
            self._wf_client.create_latency_stats(
                self._latency_sum, self._samples, created)
            self._latency_sum = 0
            self._samples = 0


class ElasticSearchRecordCountHandler(RecordCountHandler):

    def __init__(self, queue, es_client):
        super(ElasticSearchRecordCountHandler, self).__init__(queue)
        self._es_client = es_client

    def _create_record_count(self):
        created = time.time()
        self._es_client.create_record_count(self._proto_record_count, created)
        self._proto_record_count = defaultdict(
            lambda: {'success': 0, 'failure': 0})

    def _create_latency_stats(self):
        created = time.time()
        if self._samples > 0:
            self._es_client.create_latency_stats(
                self._latency_sum, self._samples, created)
            self._latency_sum = 0
            self._samples = 0
