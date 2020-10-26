#!/usr/bin/env python
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

import mock
import os
import socket
import subprocess

from axon.tests import base as test_base
from axon.traffic.servers.servers import ThreadedTCPServer, ThreadedTCPServerV6, \
    ThreadedUDPServer, ThreadedUDPServerV6, TCPRequestHandler, UDPRequestHandler, \
    IperfServer, create_server_class


class TestThreadedTCPServer(test_base.BaseTestCase):

    @mock.patch('socketserver.TCPServer.serve_forever')
    @mock.patch('socket.socket')
    def test_run_tcp_server(self, mock_socket, mock_server):
        mock_server.return_value = None
        source = '1.2.3.4'
        port = 12345
        _tcp_server = ThreadedTCPServer((source, port), TCPRequestHandler)
        _tcp_server.run()
        mock_server.assert_called()

    @mock.patch('socketserver.TCPServer.shutdown')
    @mock.patch('socket.socket')
    def test_stop_tcp_server(self, mock_socket, mock_server):
        mock_server.return_value = None
        source = '1.2.3.4'
        port = 12345
        _tcp_server = ThreadedTCPServer((source, port), TCPRequestHandler)
        _tcp_server.stop()
        mock_server.assert_called()

    @mock.patch('socket.socket')
    def test_check_tcp_server_is_alive(self, mock_socket):
        source = '1.2.3.4'
        port = 12345
        _tcp_server = ThreadedTCPServer((source, port), TCPRequestHandler)
        _tcp_server.is_alive()

    @mock.patch('socketserver.UDPServer.serve_forever')
    @mock.patch('socket.socket')
    def test_run_udp_server(self, mock_socket, mock_server):
        mock_server.return_value = None
        source = '1.2.3.4'
        port = 12345
        _tcp_server = ThreadedUDPServer((source, port), UDPRequestHandler)
        _tcp_server.run()
        mock_server.assert_called()

    @mock.patch('socketserver.UDPServer.shutdown')
    @mock.patch('socket.socket')
    def test_stop_udp_server(self, mock_socket, mock_server):
        mock_server.return_value = None
        source = '1.2.3.4'
        port = 12345
        _tcp_server = ThreadedUDPServer((source, port), TCPRequestHandler)
        _tcp_server.stop()
        mock_server.assert_called()

    @mock.patch('socket.socket')
    def test_check_udp_server_is_alive(self, mock_socket):
        source = '1.2.3.4'
        port = 12345
        _tcp_server = ThreadedUDPServer((source, port), TCPRequestHandler)
        _tcp_server.is_alive()

    @mock.patch('subprocess.Popen')
    def test_run_iperf_tcp_server(self, mock_commamnd):
        source = '1.2.3.4'
        protocol = 'TCP'
        port = 12345
        _tcp_server = IperfServer(source, protocol, port)
        _tcp_server.run()
        mock_commamnd.assert_called_with("iperf3 --server --port %s"
                                         " --bind %s" % (port, source),
                                         shell=True, stdout=subprocess.PIPE,
                                         preexec_fn=os.setsid)

    @mock.patch('subprocess.Popen')
    def test_run_iperf_udp_server(self, mock_commamnd):
        source = '1.2.3.4'
        protocol = 'UDP'
        port = 12345
        _tcp_server = IperfServer(source, protocol, port)
        _tcp_server.run()
        mock_commamnd.assert_called_with("iperf3 --server --port %s"
                                         " --bind %s --u" % (port, source),
                                         shell=True, stdout=subprocess.PIPE,
                                         preexec_fn=os.setsid)

    def test_create_tcp_server_class(self):
        protocol = 'TCP'
        port = 12345
        source = '1.2.3.4'
        server_class, args, kwargs = create_server_class(
            protocol, port, source)
        self.assertEqual(server_class, ThreadedTCPServer)

    def test_create_udp_server_class(self):
        protocol = 'UDP'
        port = 12345
        source = '1.2.3.4'
        server_class, args, kwargs = create_server_class(
            protocol, port, source)
        self.assertEqual(server_class, ThreadedUDPServer)

    def test_create_tcp_V6_server_class(self):
        protocol = 'TCP'
        port = 12345
        source = '::4'
        server_class, args, kwargs = create_server_class(
            protocol, port, source)
        self.assertEqual(server_class, ThreadedTCPServerV6)
        self.assertEqual(server_class.address_family,
                         socket.AF_INET6)

    def test_create_udp_V6_server_class(self):
        protocol = 'UDP'
        port = 12345
        source = '::4'
        server_class, args, kwargs = create_server_class(
            protocol, port, source)
        self.assertEqual(server_class, ThreadedUDPServerV6)
        self.assertEqual(server_class.address_family,
                         socket.AF_INET6)

    def test_create_iperf_tcp_server_class(self):
        server_type = 'iperf'
        protocol = 'TCP'
        port = 12345
        source = '1.2.3.4'
        server_class, args, kwargs = create_server_class(
            protocol, port, source, server_type)
        self.assertEqual(server_class, IperfServer)

    def test_create_server_class_invalid_server_type(self):
        server_type = 'fake_server_type'
        protocol = 'TCP'
        port = 12345
        source = '1.2.3.4'
        try:
            create_server_class(protocol, port, source, server_type)
        except ValueError:
            pass
