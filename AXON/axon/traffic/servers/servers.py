#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import abc
import ipaddress
import os
import signal
import six
import socket
from six.moves import socketserver
import subprocess
from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from axon.common.config import REQUEST_QUEUE_SIZE, PACKET_SIZE,\
    ALLOW_REUSE_ADDRESS


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Handle to handle HTTP Request
    """
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        message = "Hello From AXON HTTP Server \n"
        self.wfile.write(message.encode('utf-8'))
        return

    def log_message(self, format, *args):
        return


class TCPRequestHandler(socketserver.BaseRequestHandler):
    """
    Handler for TCP Requests.
    If we are using ThreadedTCPServer with the help of
    SocketServer.ThreadingMixIn feature, every TCP request will
    be handled in single thread.
    """

    def handle(self):
        data = self.request.recv(PACKET_SIZE)
        self.request.send(data)


class UDPRequestHandler(socketserver.BaseRequestHandler):
    """
    Handler for UDP Requests.
    If we are using ThreadedUDPServer with the help of
    SocketServer.ThreadingMixIn feature, every UDP request will
    be handled in single thread.
    """

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        socket.sendto(data, self.client_address)


@six.add_metaclass(abc.ABCMeta)
class Server(object):
    """
    Base Server Class
    """

    @abc.abstractmethod
    def run(self):
        """
        Start A Server
        :return: None
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Stop a server
        :return: None
        """
        pass

    @abc.abstractmethod
    def is_alive(self):
        """
        Check if server is running
        :return: True or False
        """
        pass


class ThreadedTCPServer(socketserver.ThreadingMixIn,
                        socketserver.TCPServer, Server):
    """
    This is a TCP Server which will handle every single client request
    in separate thread.
    """
    allow_reuse_address = ALLOW_REUSE_ADDRESS
    request_queue_size = REQUEST_QUEUE_SIZE

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()
        self.server_close()

    def is_alive(self):
        pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer, Server):
    """Handle requests in a separate thread."""

    allow_reuse_address = ALLOW_REUSE_ADDRESS
    request_queue_size = REQUEST_QUEUE_SIZE

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()
        self.server_close()

    def is_alive(self):
        pass


class ThreadedUDPServer(socketserver.ThreadingMixIn,
                        socketserver.UDPServer, Server):
    """
    This is a UDP Server which will handle every single client request
    in separate thread.
    """
    allow_reuse_address = ALLOW_REUSE_ADDRESS
    request_queue_size = REQUEST_QUEUE_SIZE

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()
        self.server_close()

    def is_alive(self):
        pass


class ThreadedHTTPServerV6(ThreadedHTTPServer):
    address_family = socket.AF_INET6


class ThreadedTCPServerV6(ThreadedTCPServer):
    address_family = socket.AF_INET6


class ThreadedUDPServerV6(ThreadedUDPServer):
    address_family = socket.AF_INET6


class IperfServer(Server):
    """
    Class to manage Iperf Server
    """
    def __init__(self, source, protocol, port):
        self._protocol = protocol
        self._port = port
        self._p_child = None
        self._source = source

    def run(self):
        command = "iperf3 --server --port %d --bind %s" % \
                  (self._port, self._source)
        if self._protocol == "UDP":
            command += " --u"
        self._p_child = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE,
            preexec_fn=os.setsid)

    def stop(self):
        pid = self._p_child.pid
        if self.is_alive():
            os.killpg(os.getpgid(pid), signal.SIGTERM)

    def is_alive(self):
        return self._p_child.poll() is None


def create_server_class(protocol, port, source, server_type='socket'):
    """
    Create server object
    :param protocol: protocol on which server works
    :type protocol: str
    :param port: port on which server listen
    :type port: int
    :param server_type: socket server or iperf server
    :type server_type: int
    :return: Server object
    :rtype: Server
    """
    if protocol == "TCP" and server_type == "socket":
        server_class = ThreadedTCPServerV6 \
            if ipaddress.ip_address(source).version == 6 \
            else ThreadedTCPServer
        args = ((source, int(port)), TCPRequestHandler)
        kwargs = {}
    elif protocol == "UDP" and server_type == "socket":
        server_class = ThreadedUDPServerV6 \
            if ipaddress.ip_address(source).version == 6 \
            else ThreadedUDPServer
        args = ((source, int(port)), UDPRequestHandler)
        kwargs = {}
    elif server_type == "iperf":
        server_class = IperfServer
        args = (source, protocol, port)
        kwargs = {}
    elif protocol == 'HTTP':
        server_class = ThreadedHTTPServerV6 \
            if ipaddress.ip_address(source).version == 6 \
            else ThreadedHTTPServer
        args = ((source, int(port)), HTTPRequestHandler)
        kwargs = {}
    else:
        raise ValueError("Invalid Value (%s, %s, %s) for Server" %
                         (protocol, port, server_type))
    return server_class, args, kwargs
