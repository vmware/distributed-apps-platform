#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
from six.moves import queue as Queue
import sys
import threading
import time


from axon.client.traffic_elements import TrafficRule, \
    Endpoint, Port, Protocol, Action, Connected


_lock_debug = False  # Default to False to avoid huge log files
global_lock = threading.Lock()  # Not currently used, but left for examples.
static_lock = threading.Lock()
store_func_exception_args = False
log = logging.getLogger('utilities')


def truncate_str(tr_str, num_chars, terminator=None):
    """
    Truncates tr_str at num_chars and appends a terminator message.
    If num_chars == 0, return the original string.
    """

    default_terminator = "<TRUNCATED>"
    if terminator is None:
        terminator = default_terminator
    if num_chars == 0 or len(tr_str) <= num_chars:
        return tr_str
    return "%s%s" % (tr_str[:num_chars], terminator)


def create_mesh_ping_topo_from_cidr(hosts):
    """This function Returns list of rules for mesh ping"""
    rule_list = []
    for index, host in enumerate(hosts):
        destinations = hosts[index + 1: len(hosts)] + hosts[0: index]
        for destination in destinations:
            rule_list.append(
                TrafficRule(Endpoint(host), Endpoint(destination),
                            Port(12345), Protocol.TCP,
                            Connected.CONNECTED, Action.ALLOW)
            )
            rule_list.append(
                TrafficRule(Endpoint(host), Endpoint(destination),
                            Port(12345), Protocol.UDP,
                            Connected.CONNECTED, Action.ALLOW)

            )
    return rule_list


def as_list(obj, tuple_to_list=False, if_none=NotImplemented):
    """
    This is useful to allow arguments that are theoretically lists, but
    tend to be single items in practice.  As syntactic sugar, we allow
    passing in these single items in some cases.  For example, multiple
    allowed statuses or zones might be passed into the below functions,
    but it tends to just be one:
    """
    if obj is None:
        if if_none == NotImplemented:
            # Here NotImplemented is a magic value indicating
            # no-special casing, we will return [None]
            pass
        elif type(if_none) == type and issubclass(if_none, Exception):
            # Note that issubclass raises a TypeError if a non-class is
            # passed in, thus we have to check the type first
            raise if_none("as_list received None as input")
        else:
            return if_none
    if not hasattr(obj, '__iter__') or (tuple_to_list and type(obj) is tuple):
        obj = [obj]
    return obj


def withlock(getlock):
    '''
    Function decorator to introduce locking
    Normal usage (no logging):
        @withlock(lambda *args, **kwargs: global_lock)
        def your_function(...)
    To enable logging of lock operations:
        @withlock(lambda *args, **kwargs: (global_lock, True))
        def your_function(...)
    To enable logging of lock operations, but disable logging for lock waits:
        @withlock(lambda *args, **kwargs: (global_lock, True, False))
        def your_function(...)
    '''
    def func_locker(func):
        def locked_func(*args, **kwargs):
            info_list = as_list(getlock(*args, **kwargs))
            lock = info_list[0]
            if len(info_list) < 2:
                flag_log_msg = _lock_debug
            else:
                flag_log_msg = info_list[1]
            if len(info_list) < 3:
                flag_lock_wait_msg = True
            else:
                flag_lock_wait_msg = info_list[2]
            what = "%s() with %s" % (func.__name__, lock)
            if flag_log_msg:
                log.debug("Trying to lock: %s" % what)
            if not lock.acquire(False):
                if flag_lock_wait_msg:
                    log.warn("Waiting on lock: %s" % what)
                start = time.time()
                lock.acquire()
                duration = time.time() - start
                if flag_lock_wait_msg:
                    log.warn("Waited on lock for %.3fs: %s" % (duration, what))
            if flag_log_msg:
                log.debug("Lock acquired: %s" % what)
            try:
                ret = func(*args, **kwargs)
            finally:
                if flag_log_msg:
                    log.debug("Unlocking: %s" % what)
                lock.release()
            return ret
        locked_func.__name__ = "locked_%s" % func.__name__
        return locked_func
    return func_locker


class FuncException(Exception):
    args = None
    kwargs = None

    def __init__(self, func_name, args, kwargs, exc_repr, exc_info,
                 thread=None, truncate_chars=None):
        # Save the information so that it can be used later in messages
        # We don't save the details, since they are not used anywhere
        # yet (though there are some advantages, retrying becomes very easy),
        # and this may prevent a large amount of garbage collection

        # Sometimes (like in scale tests) the args list can be thousands
        # of items long. We don't want to print such huge lists, so
        # truncate past a certain point.
        DEFAULT_TRUNCATE_CHARS = 200
        if truncate_chars is None:
            truncate_chars = DEFAULT_TRUNCATE_CHARS
        if store_func_exception_args:
            self.args = args
            self.kwargs = kwargs
        self.exc_info = exc_info
        args = truncate_str(str(args), truncate_chars)
        kwargs = truncate_str(str(kwargs), truncate_chars)
        thread_str = thread and "[thread=%s] " % thread or ""
        try:
            arg_str = str(args)
        except Exception as e:
            arg_str = '<str() triggers error %s>' % e
        try:
            kwarg_str = str(kwargs)
        except Exception as e:
            kwarg_str = '<str() triggers error %s>' % e
        self.value = ("%s%s(args=%s, kwargs=%s): Exception %s" %
                      (thread_str, func_name, arg_str, kwarg_str, exc_repr))

    def __repr__(self):
        return "<FuncException %s>" % self.value

    __str__ = __repr__


class AbortException(FuncException):
    pass


class ParallelWork():
    log = logging.getLogger('ParallelWork')

    def __init__(self, work=None, count=None, daemon=True):
        if work is None:
            work = []
        if count is None or count > len(work):
            count = len(work)

        # Assumes work is a tuple of (func, args, kwargs)
        self.results = []
        self.work = work
        self.count = count
        self.wm = WorkManager(self.count, daemon=daemon)
        self.workers = [self.wm.run(f, *a, **kw) for (f, a, kw) in work]

    def start(self, *args, **kwargs):
        self.wm.start(*args, **kwargs)

    def stop(self, *args, **kwargs):
        return self.wm.stop(*args, **kwargs)

    def get(self, raise_exceptions=False, **stop_kwargs):
        # Stop the threads before get() that can raise exc's
        self.wm.stop(**stop_kwargs)
        try:
            self.results = [w.get(raise_exception=raise_exceptions)
                            for w in self.workers]
        finally:
            # This is to avoid memory leaks when the called functions
            # return exceptions
            del self.wm
        return self.results

    @classmethod
    def Background(cls, func, *args, **kwargs):
        pwm = cls.Start(work=[(func, args, kwargs)], count=1, daemon=True)
        pwm.wm.work_done(abort=False)
        return pwm

    @classmethod
    def Start(cls, *args, **kwargs):
        pwm = cls(*args, **kwargs)
        pwm.start()
        return pwm

    @classmethod
    def Do(cls, *args, **kwargs):
        get_keys = ['raise_exceptions']
        get_kwargs = dict((k, kwargs.pop(k)) for k in get_keys if k in kwargs)
        pwm = cls.Start(*args, **kwargs)
        return pwm.get(**get_kwargs)


class WorkManager():
    log = logging.getLogger('WorkManager')
    work_queue = None
    threads = None

    class WorkQueue(Queue.Queue):
        log = logging.getLogger('WorkQueue')

        # Use raise_exception=True if you want to catch exceptions
        # Since not-raising is a silly default, add another default to
        # always warn on exceptions until this is handled properly
        def get(self, raise_exception=False, warn_exception=True):
            obj = Queue.Queue.get(self)
            if isinstance(obj, FuncException):
                if raise_exception:
                    raise obj
                if warn_exception:
                    self.log.exception("Not raising exception: %s" % obj)
            return obj

    def __init__(self, count=4, daemon=True):
        self.count = count
        self.daemon = daemon
        self._lock = threading.Lock()
        self.initialize()

    def initialize(self):
        self._abort = False
        self._work_done = False
        self._exceptions = []
        if self.work_queue is None:
            self.work_queue = Queue.Queue()

    @withlock(lambda s, *unused_a, **unused_kw: s._lock)
    def start(self):
        if self.threads:
            self.log.warn("Cannot start WorkManager again, call stop "
                          "before starting again")
            return
        self.initialize()
        self.threads = [threading.Thread(target=self._worker)
                        for _ in range(self.count)]
        for th in self.threads:
            th.setDaemon(self.daemon)
            th.start()

    # Useful for calling the method as it is without changing the params and
    # the method only needs to prepended to the args/kwargs
    def run(self, func, *args, **kwargs):
        if not self._work_done and self.work_queue:
            q = None if func is None else self.WorkQueue()
            self.work_queue.put([q, func, args, kwargs])
            return q
        else:
            self.log.warn("Call start method again to init threads before "
                          "run, as stop or work_done is already called")
            return

    def _worker(self):
        while True:
            (q, func, args, kwargs) = self.work_queue.get()
            if func is None:
                self.work_queue.task_done()
                break
            elif not self._abort:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    thread = threading.current_thread().name
                    result = FuncException(
                        func.__name__, args, kwargs, repr(e),
                        sys.exc_info(), thread=thread)
                    self.log.exception("%s: %s" % (result, e))
                    self._exceptions.append(result)
                q.put(result)
                self.work_queue.task_done()
            elif self._abort:
                thread = threading.current_thread().name
                msg = ("Aborted all pending queued func using "
                       "stop(abort=True) or work_done(abort=True)")
                result = AbortException(func.__name__, args, kwargs,
                                        msg, thread=thread)
                self._exceptions.append(result)
                q.put(result)
                self.work_queue.task_done()

    @withlock(lambda s, *a, **kw: s._lock)
    def work_done(self, abort=False):
        return self.__stop_threads(abort=abort)

    def __stop_threads(self, abort=False):
        if self._work_done:
            self.log.warn("Cannot stop already stopped WorkManager")
            return
        self._work_done = True
        if abort:
            self.log.warn("!!! Aborting all remaining queued funcs for "
                          "execution, all the q.get() could block !!!")
            self._abort = True

        # Passing None to work_queue will break the loop and stop the worker
        # after all the funcs that are currently queued are completed
        for _ in range(self.count):
            self.work_queue.put([None, None, None, None])
        del self.threads

    @withlock(lambda s, *a, **kw: s._lock)
    def stop(self, abort=False):
        """
        Passing abort=True, stops the workers after current set of funcs
        causing the list of results to be truncated, so all the q.get()
        may block
        >>> def foo():
        ...    time.sleep(0.5)
        >>> pwm = ParallelWork.Start([(foo, [], {})]*2, count=1)
        >>> pwm.get(abort=True)
        [None, ...Aborted all pending queued func using...]
        """
        if self.work_queue is None:
            self.log.warn("Cannot stop already stopped WorkManager")
            return

        self.__stop_threads(abort=abort)
        try:
            # Setting work_queue to None, to avoid rejoining the same queue, if
            # called stop from multiple threads
            if self.work_queue:
                self.work_queue.join()
                del self.work_queue
        finally:
            pass

        aborted = []
        for x in self._exceptions:
            if isinstance(x, AbortException):
                aborted.append(x)
            else:
                self.log.exception("Exception: %s" % x)
        if aborted:
            self.log.warn("Work aborted: %s" % aborted)


class Thread(threading.Thread):
    """
    This class wraps threading.Thread so that join() returns the asynchronous
    function's return value.  It has the same interface as threading.Thread.

    >>> def a(b, c, d=None, e=None):
    ...     return b, c, d, e
    >>> t = Thread(target=a, args=(1,2), kwargs={"d": 3, "e": 4})
    >>> t.start()
    >>> t.join()
    (1, 2, 3, 4)
    """

    retval = None

    def __init__(self, group=None, target=None, name=None, args=None,
                 kwargs=None):
        """
        Overrides target to self.get_retval, and passes arguments to that
        function.
        """
        super(Thread, self).__init__(group=group, target=self.__store_retval,
                                     args=[target, args, kwargs], name=name)

    def __store_retval(self, func, args, kwargs):
        """
        Wrapper function to execute and store return value.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        self.retval = func(*args, **kwargs)

    def join(self, timeout=None):
        """
        Performs the same function as threading.Thread.join, but also returns
        the function's retval.
        """
        super(Thread, self).join(timeout=timeout)
        return self.retval
