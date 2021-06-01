#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.


import http.server as hserver
import json
import logging
import socket
import threading
import time

from lydian.apps import config as config
from lydian.traffic.connection import Connection

log = logging.getLogger(__name__)


class Server(Connection):

    def __init__(self, port=None, max_conns=None,
                 handler=None, verbose=False, ipv6=False):
        """
        A basic TCP Server connection listener with default echo reply
        message handler.
        """
        self.host = ''   # blank on server side
        self.port = self.DEFAULT_TCP_SERVER_PORT if port is None else port
        self.max_conns = self.MAX_CONNS if max_conns is None else max_conns
        self._handler = self.echo_handler if handler is None else handler

        super(Server, self).__init__(verbose=verbose)

        # Don't create a socket until we are ready to bind.
        self.socket = None
        self.ipv6 = ipv6

    def echo_handler(self, payload):
        raise NotImplementedError("Handler not implemented in %s" % self.__class__.__name__)


class TCPServer(Server):

    def _create_socket(self):
        """
        Returns a simple TCP server socket.
        """
        sock_type = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        self.socket = socket.socket(sock_type, socket.SOCK_STREAM)

    def start(self):
        """
        API to start server at the requested port and other settings.
        """
        try:
            self.clear_event()
            # Create a socket
            self._create_socket()

            # Bind ot the port
            self.socket.bind((self.host, self.port))

            # accept call from client
            self.socket.listen(self.max_conns)

            if self.verbose:  # TODO : more stringent check
                self.log.info(
                    "TCP Server started on %s:%s",
                    self.host,
                    self.port)

            while not self.is_event_set():
                conn, addr = self.socket.accept()
                if self.verbose:
                    msg = "Connection request received from: %s:%s" % (addr[0], addr[1])
                    self.log.info(msg)
                self._handler(conn)
        except Exception as err:
            log.error("Error in starting (TCP) server : %r", err)
        finally:
            self.close()

    def echo_handler(self, conn):
        """
        A simple default echo message handler.
        """
        data = conn.recv(self.MAX_PAYLOAD_SIZE)
        conn.send(data)  # send same data back as echo
        conn.close()    # close immediately.


class UDPServer(Server):

    def _create_socket(self):
        """
        Returns a simple TCP server socket.
        """
        sock_type = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        self.socket = socket.socket(sock_type, socket.SOCK_DGRAM)

    def start(self):
        """
        API to start server at the requested port and other settings.
        """
        try:
            self.clear_event()
            # Create a socket
            self._create_socket()

            # Bind at the port
            self.socket.bind((self.host, self.port))

            if self.verbose:  # TODO : more stringent check
                self.log.info("UDP Server started on %s:%s", self.host, self.port)

            while not self.is_event_set():
                data, addr = self.socket.recvfrom(self.MAX_PAYLOAD_SIZE)
                if self.verbose:
                    msg = "Connection request received from: %s:%s" % (addr[0], addr[1])
                    self.log.info(msg)
                self._handler(data, addr)
        except Exception as err:
            log.error("Error in starting (UDP) server : %r", err)
        finally:
            self.close()

    def echo_handler(self, data, addr):
        """
        A simple default echo message handler.
        """
        if data:
            self.socket.sendto(data, addr)  # send same data back as echo


try:
    _HTTPServer = hserver.ThreadingHTTPServer
except AttributeError:
    import socketserver
    class _HTTPServer(socketserver.ThreadingMixIn, hserver.HTTPServer):
        pass


class _HTTPServerV6(_HTTPServer):
    address_family = socket.AF_INET6


class HTTPServer(Server):
    """
    Basic HTTP Server
    """
    BLOCKING_WAIT_TIME = 3

    class _HTTPRequestHandler(hserver.SimpleHTTPRequestHandler):

        def log_message(self, format, *args):
            pass  # Log disabled.

        def _set_headers(self):
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

        def do_HEAD(self):
            self._set_headers()

        def do_GET(self):
            self.send_response(200)
            self._set_headers()
            response = json.dumps({
                'status': 200,
                'payload': self.path[1:]    # Return the path as response.
                })

            self.wfile.write(bytes(response, 'utf-8'))

    def __init__(self, *args, **kwargs):
        super(HTTPServer, self).__init__(*args, **kwargs)
        self.verbose = kwargs.get('verbose', False)
        if self.verbose:
            self.handler = hserver.SimpleHTTPRequestHandler
        else:
            self.handler =  self._HTTPRequestHandler

        self._Server = _HTTPServerV6 if self.ipv6 else _HTTPServer
        self.httpd = None
        self._thread = None
        self.clear_event()

    def start(self, blocking=True):
        """ Starts HTTP Server. """
        self.httpd = self._Server(("", self.port), self.handler)
        self._thread = threading.Thread(target=self.httpd.serve_forever,
                                        daemon=True)
        self._thread.start()
        if blocking:
            # TCP / UDP server are blocking by default. blocking is set
            # on by default here to match that behavior.
            self._thread.join()

    def stop(self):
        """ Stops HTTP Server. """
        self.set_event()
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self._thread:
            self._thread.join(config.get_param('THREADS_JOIN_TIMEOUT'))
        self._thread, self.httpd = None, None
