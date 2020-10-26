import logging
from multiprocessing.pool import ThreadPool

from axon.db.recorder_factory import RecorderFactory
from axon.common import config as conf


log = logging.getLogger(__name__)


def process_record_queues(args):
    queue = args[0]
    recorders = args[1]
    while True:
        try:
            t_record = queue.get()
            for recorder in recorders:
                recorder.write(t_record)
        except Exception:
            # TODO : change it to specific exception when queue is empty
            # Don't give error when no data is being generated.
            log.exception("Error in listening Traffic Record Queue")


class DBPoolManager(object):
    """
    This class act as a deamon to read traffic record queue and to
    write record to the db recorder provided
    """

    def __init__(self, record_queue):
        self._db_recorders = RecorderFactory.get_recorders()
        self._record_queue = record_queue

    def run(self):
        thread_pool = ThreadPool(conf.RECORD_UPDATER_THREAD_POOL_SIZE)
        thread_pool.map(process_record_queues,
                        [(self._record_queue,
                          self._db_recorders)] *
                        conf.RECORD_UPDATER_THREAD_POOL_SIZE)
