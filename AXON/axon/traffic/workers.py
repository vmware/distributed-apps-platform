#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import abc
import multiprocessing as mp
from threading import Thread
import six
import logging


@six.add_metaclass(abc.ABCMeta)
class Worker(object):
    """
    A Thread or Process which holds the server/client and
    manages its life cycle
    """

    @abc.abstractmethod
    def run(self):
        """
        Run a server
        :return: None
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Stop the Server inside it
        :return: None
        """
        pass

    @abc.abstractmethod
    def is_running(self):
        """
        Check if Server Container is alive
        :return: True or False
        """
        pass


class WorkerThread(Thread, Worker):
    """
    Run A Server/Client Inside a thread
    """
    _log = logging.getLogger(__name__)

    def __init__(self, traffic_class, args=(), kwargs=None):
        super(WorkerThread, self).__init__()
        self.__traffic_class = traffic_class
        self.__class_args = args
        self.__class_kwargs = kwargs
        self.__traffic_obj = None

    def run(self):
        try:
            self._log.info("Starting thread with args %s %s %s" %
                           (self.__traffic_class, self.__class_args,
                            self.__class_kwargs))
            self.__traffic_obj = self._traffic_class(
                *self.__class_args, **self.__class_kwargs)
            self.__traffic_obj.run()
        except Exception:
            self._log.exception("Exception happened during starting Thread"
                                " with args %s %s %s" %
                                (self.__traffic_class, self.__class_args,
                                 self.__class_kwargs))

    def stop(self):
        self.__traffic_obj.stop()

    def is_running(self):
        return self.isAlive()


class WorkerProcess(mp.Process, Worker):
    """
    Run a server/Client inside a process
    """
    _log = logging.getLogger(__name__)

    def __init__(self, traffic_class, args=(), kwargs=None):
        super(WorkerProcess, self).__init__()
        self.__traffic_class = traffic_class
        self.__class_args = args
        self.__class_kwargs = kwargs
        self.__traffic_obj = None

    def run(self):
        try:
            self._log.info("Starting Process with args %s %s %s" %
                           (self.__traffic_class, self.__class_args,
                            self.__class_kwargs))
            self.__traffic_obj = self.__traffic_class(
                *self.__class_args, **self.__class_kwargs)
            self.__traffic_obj.run()
        except Exception:
            self._log.exception("Exception happened during starting Process"
                                " with args %s %s %s" %
                                (self.__traffic_class, self.__class_args,

                                 self.__class_kwargs))

    def stop(self):
        self.terminate()

    def is_running(self):
        return self.is_alive()
