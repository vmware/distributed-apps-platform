#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import json
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

    CONNECTION_TIMEOUT = 1.8
    FREQUENCY = 30       # 30 pings per minute.
    PAYLOAD = 'Rampur!!'
    PING_INTERVAL = 2   # default request rate is 30ppm

    def __init__(self, server, port, verbose=False, handler=None,
                 interval=None, ipv6=None, payload=None, tries=None,
                 sockettimeout=None, frequency=30, attempts=None):
        """
        A simple TCP client which binds to a specified host and port.
        """
        self.server = server
        self.port = int(port)

        self._handler = handler or self.echo_validator
        self.ipv6 = ipv6 or is_ipv6_address(self.server)

        self._payload = payload or self.PAYLOAD
        self._tries = tries or None
        self._sockettimeout = sockettimeout or self.CONNECTION_TIMEOUT
        self.attempts = attempts or 1

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

    def echo_validator(self, payload, data, latency, error=None):
        """
        Ping Validator
        """
        try:
            assert(data == self.PAYLOAD)
            log.info("Sent : %s Received : %s, taken %s ms", self.PAYLOAD, data, latency)
        except AssertionError as _:
            _ = error
            raise PingValidationError()

    def recv_all(self):
        fragments = []
        while True:
            chunk = self.socket.recv(self.MAX_PAYLOAD_SIZE)
            if not chunk:
                break
            fragments.append(chunk)
        return b''.join(fragments)

    def start(self, payload=None, tries=None):
        if not self.stopped():
            log.info("Traffic client alredy running for server - %s:%s",
                     self.server, self.port)
            return
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
        sock_type = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        self.socket = socket.socket(sock_type, socket.SOCK_STREAM)
        self.socket.settimeout(self.sockettimeout)

    def send_and_recv(self, payload, recv_method):
        attempts = self.attempts
        data, latency, error = None, 0, None
        while attempts:
            try:
                attempts -= 1
                self._create_socket()
                start_time = time.time()
                self.socket.connect((self.server, self.port))
                self.socket.send(payload)
                data = recv_method()
                latency = round((time.time() - start_time) * LATENCY_RESOLUTION, 2)
                if self.verbose:
                    msg = "Ping to %s:%s PASS. Payload / data - %s/%s" % (
                           self.server, self.port, payload, data)
                    log.info(msg)
                break   # finally is still executed.
            except Exception as err:
                error = '%s' % err
                if self.verbose:
                    msg = ("Ping to %s:%s FAIL. Payload / data - %s/%s ."
                           " ERROR - %r") % (
                           self.server, self.port, payload, data, err)
                    log.info(msg)
                    if attempts:
                        count = self.attempts - attempts + 1
                        log.debug('Retrying attempt %s/%s', count, self.attempts)
            finally:
                # close socket connection
                self.socket_close()

        return data, latency, error

    def ping(self, payload):
        try:
            payload = self._prepare_payload(payload)
            data, latency, error = self.send_and_recv(payload, recv_method=self.recv_all)
            self._handler(payload, data, latency, error)
        except Exception as err:
            if self.verbose:
                log.info('Ping Error - %r', err)


class UDPClient(Client):

    def _create_socket(self):
        """
        Returns a simple TCP server socket.
        """
        sock_type = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        self.socket = socket.socket(sock_type, socket.SOCK_DGRAM)
        self.socket.settimeout(self.sockettimeout)

    def send_and_recv(self, payload):
        attempts = self.attempts
        data, latency, error = None, 0, None
        while attempts:
            try:
                attempts -= 1
                self._create_socket()
                start_time = time.time()
                self.socket.sendto(payload, (self.server, self.port))
                data, _ = self.socket.recvfrom(self.MAX_PAYLOAD_SIZE)
                latency = round((time.time() - start_time) * LATENCY_RESOLUTION, 2)
                if self.verbose:
                    msg = "Ping to %s:%s PASS. Payload / data - %s/%s" % (
                           self.server, self.port, payload, data)
                    log.info(msg)
                break   # finally is still executed.
            except Exception as err:
                error = '%s' % error
                if self.verbose:
                    msg = ("Ping to %s:%s FAIL. Payload / data - %s/%s ."
                           " ERROR - %r") % (
                           self.server, self.port, payload, data, err)
                    log.info(msg)
                    if attempts:
                        count = self.attempts - attempts + 1
                        log.debug('Retrying attempt %s/%s', count, self.attempts)
            finally:
                self.socket_close()

        return data, latency, err

    def ping(self, payload):
        latency = 0
        try:
            payload = self._prepare_payload(payload)
            data, latency, error = self.send_and_recv(payload)
            self._handler(payload, data, latency, error)
        except Exception as err:
            if self.verbose:
                log.info('Ping Error - %r', err)


class HTTPClient(TCPClient):

    def _prepare_payload(self, payload):
        payload = "GET /%s HTTP/1.1\r\n\r\n\r\n" % payload
        return payload.encode('utf-8') if is_py3() else payload

    def fetch(self):
        _data = self.recv_all()
        _data = _data.decode().splitlines()
        if '200 OK' in str(_data[0]):
            data = json.loads(_data[-1])['payload']
        else:
            data = None
        return data

    def ping(self, payload):
        try:
            _payload = self._prepare_payload(payload)
            data, latency, error = self.send_and_recv(_payload,
                                               recv_method=self.fetch)
            self._handler(payload, data, latency, error)
        except Exception as err:
            if self.verbose:
                log.info('Ping Error - %r', err)
