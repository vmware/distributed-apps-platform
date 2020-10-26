'''
Unit test for Monitor app.
'''
import logging
import queue
import time
import unittest

from axon.apps.monitor import ResourceMonitor


log = logging.getLogger(__name__)


class TestResourceMonitorApp(unittest.TestCase):

    def setUp(self):
        super(TestResourceMonitorApp, self).setUp()
        self._rq = queue.Queue()   # Queue()
        self._monitor = ResourceMonitor(rqueue=self._rq)

    def test_resource_monitor(self):
        self._monitor.start() # start monitoring

        time.sleep(10)
        self._monitor.stop()  # stop monitoring

        recs = []
        while True:
            try:
                rec = self._rq.get(block=False)
                recs.append(rec)
            except queue.Empty:
                break

        assert recs, "No records generated!"
