"""
Utilties to temporarily enter linux namespaces.

Demo:

$ ip netns add testns
$ ip link add veth0 type veth peer name veth1
$ ip link set veth1 netns testns
$ ip link list | grep veth
315: veth0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
$ ip netns exec testns ip link list | grep veth
314: veth1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
$ python
...
>>> from lydian.utils.nsenter import *
>>> print(os.popen('ip link list | grep veth').read().strip())
315: veth0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
>>> with namespace('/var/run/netns/testns', 'net'):
...     print(os.popen('ip link list | grep veth').read().strip())
...
314: veth1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
>>>
>>> print(os.popen('ip link list | grep veth').read().strip())
315: veth0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
>>>
"""

import contextlib
import ctypes.util
import logging
import os

logger = logging.getLogger(__name__)
LIBC = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
VALID_NAMESPACES = frozenset(['ipc', 'mnt', 'net', 'pid', 'user', 'uts'])


def setns(fd):
    """See http://man7.org/linux/man-pages/man2/setns.2.html"""
    if LIBC.setns(fd, 0) == -1:
        err = ctypes.get_errno()
        raise OSError(err, errno.errorcode[err])


@contextlib.contextmanager
def fdopen(path):
    """Open a read-only fd to <path>"""
    fd = os.open(path, os.O_RDONLY)
    try:
        yield fd
    finally:
        os.close(fd)


@contextlib.contextmanager
def namespace(nspath, nstype, verbose=False):
    """Enter the provided namespace"""
    if nstype not in VALID_NAMESPACES:
        raise ValueError("invalid namespace type %r" % nstype)

    with fdopen("/proc/self/ns/%s" % nstype) as original_ns:
        with fdopen(nspath) as new_ns:
            if verbose:
                logger.debug("Entering %s namespace %s", nstype,
                             nspath)
            setns(new_ns)
        try:
            yield
        finally:
            if verbose:
                logger.debug("Leaving %s namespace %s", nstype, nspath)
            setns(original_ns)

Namespace = namespace