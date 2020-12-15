#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import logging
import socket
import time

from urllib.request import urlopen

from lydian.traffic.connection import Connection
from lydian.utils.common import is_ipv6_address, is_py3

log = logging.getLogger(__name__)

LATENCY_RESOLUTION = 1000   # Save Latency in milliseconds.

class PingValidationError(Exception):
    pass


class Client(Connection):
    PAYLOAD = 'Rampur!!'
    CONNECTION_TIMEOUT = 1.8
    FREQUECY = 30       # 30 pings per minute.
    PING_INTERVAL = 2   # default request rate is 30ppm

    def __init__(self, server, port, verbose=False, handler=None,
                 interval=None, ipv6=None, payload=None, tries=None,
                 sockettimeout=None, frequency=30):
        """
        A simple TCP client which binds to a specified host and port.
        """
        self.server = server
        self.port = int(port)

        self._handler = handler or self.echo_validator
        self._ipv6 = ipv6 or is_ipv6_address(self.server)

        self._payload = payload or self.PAYLOAD
        self._tries = tries or None
        self._sockettimeout = sockettimeout or self.CONNECTION_TIMEOUT

        # Set frequency
        try:
            assert isinstance(frequency, int)
            assert 1 <= frequency <= 60, "Invalid frequency"
            self._frequency = frequency or 30
        except Exception as err:
            self._frequency = self.FREQUENCY
            log.error("Invalid frequency %s, ignored. Default 30 shall be"
                      " used.", frequency)

        # Set ping interval. Takes precedence over frequency.
        try:
            self.interval = int(interval)
        except (ValueError, TypeError) as err:
            _ = err
            self.interval = 60 / self.frequency

        super(Client, self).__init__(verbose=verbose)

    @property
    def payload(self):
        """ Payload for ping. """
        return self._payload

    @property
    def tries(self):
        """ Number of total pings to be sent."""
        return self._tries

    @property
    def sockettimeout(self):
        """ Socket timetout """
        return self._sockettimeout

    @property
    def frequency(self):
        """ Number of pings per minute (PPM). Default is 30"""
        return self._frequency

    ping_count = tries

    def echo_validator(self, payload, data, latency):
        """
        Ping Validator
        """
        try:
            assert(data == self.PAYLOAD)
            log.info("Sent : %s Received : %s, taken %s ms", self.PAYLOAD, data, latency)
        except AssertionError as err:
            _ = err
            raise PingValidationError()

    def start(self, payload=None, tries=None):
        self.clear_event()
        payload = payload or self.payload
        tries = tries or self.tries
        try:
            tries = int(tries) if tries is not None else None
        except Exception as err:
            if not tries:
                log.error("tries %s is invalid. Client will run forever."
                          " Error: %s", tries, err)
            tries = None

        while not self.is_event_set():
            if tries is not None:
                if not tries:
                    break
                else:
                    tries -= 1
            self.ping(payload)
            if self.interval:
                time.sleep(self.interval)

    def ping(self, payload):
        raise NotImplementedError("Ping not implemented in %s" %
                                  self.__class__.__name__)

    def _prepare_payload(self, payload):
        return payload.encode('utf-8') if is_py3() else payload


class TCPClient(Client):

    def _create_socket(self):
        """
        Returns a simple TCP server socket.
        """
        sock_type = socket.AF_INET6 if self._ipv6 else socket.AF_INET
        self.socket = socket.socket(sock_type, socket.SOCK_STREAM)
        self.socket.settimeout(self.sockettimeout)

    def ping(self, payload):
        data = None
        latency = 0
        try:
            start_time = time.time()
            # create socket
            self._create_socket()
            self.socket.connect((self.server, self.port))
            payload = self._prepare_payload(payload)
            self.socket.send(payload)
            data = self.socket.recv(self.MAX_PAYLOAD_SIZE)
            # latency in milliseconds
            latency = round((time.time() - start_time) * LATENCY_RESOLUTION, 2)
            # close socket connection
            self.socket_close()

            if self.verbose:
                msg = "ping to %s:%s pass. data - %r" % (
                    self.server, self.port, data)
                # self.log.info(msg)
            return data  # TODO : is is needed ?
        except Exception as err:
            msg = "ping to %s:%s failed. Error - %r" % (
                self.server, self.port, err)
            if self.verbose:
                log.error(msg)
        finally:
            self._handler(payload, data, latency)


class UDPClient(Client):

    def _create_socket(self):
        """
        Returns a simple TCP server socket.
        """
        sock_type = socket.AF_INET6 if self._ipv6 else socket.AF_INET
        self.socket = socket.socket(sock_type, socket.SOCK_DGRAM)
        self.socket.settimeout(self.sockettimeout)

    def ping(self, payload):
        latency = 0
        try:
            start_time = time.time()
            # create socket
            self._create_socket()
            addr = (self.server, self.port)
            payload = self._prepare_payload(payload)
            self.socket.sendto(payload, addr)
            try:
                data, server = self.socket.recvfrom(self.MAX_PAYLOAD_SIZE)
            except Exception:
                data, server = None, None
            _ = server
            # latency in milliseconds
            latency = round((time.time() - start_time) * LATENCY_RESOLUTION, 2)
            # close socket connection
            self.socket_close()
            if self.verbose:
                msg = "ping to %s:%s pass. data - %r" % (
                    self.server, self.port, data)
                self.log.info(msg)
            return data
        except Exception as err:
            if self.verbose:
                log.error("ping to %s:%s failed. Error - %r",
                          self.server, self.port, err)
        finally:
            self._handler(payload, data, latency)


class HTTPClient(Client):

    def ping(self, payload):
        latency = 0
        try:
            start_time = time.time()
            data = ''.encode('utf-8')
            url = 'http://%s:%s' % (self.server, self.port)
            status = urlopen(url).code
            data = payload if status == 200 else data
            # latency in milliseconds
            latency = round((time.time() - start_time) * LATENCY_RESOLUTION, 2)
        except Exception as err:
            if self.verbose:
                log.error("ping to %s:%s failed. Error - %r",
                          self.server, self.port, err)
        finally:
            self._handler(payload, data, latency)
