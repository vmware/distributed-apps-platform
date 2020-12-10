#!/usr/bin/env python
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
A simple traffic utility which starting standalone TCP/UDP client/servers.

USAGE:
---------
# Start TCP Server on port 5649
$ python -mlydian.utils.traffic -t -v -s -p localhost 5649

# Start TCP Client to send ping to above server.
$ python -mlydian.utils.traffic -t -v -c -p localhost 5649
'''

import argparse
import os
import signal
import sys

from lydian.traffic import client as hclient
from lydian.traffic import server as hserver
from lydian.utils.common import is_py3


def _print(msg):
    if is_py3():
        print(msg)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-s', '--server', action="store_true",
        help="Run server")
    parser.add_argument(
        '-c', '--client', action="store_true",
        help="Run client")
    parser.add_argument(
        '-i', '--ipv6', action="store_true",
        help="Use IPv6 client / servers.")
    parser.add_argument(
        '-l', '--load',
        help="Payload for traffic.")
    parser.add_argument(
        '-n', '--num_pings',
        help="Number of pings to send.")
    parser.add_argument(
        '-p', '--port', nargs='+',
        help="Port to connect")
    parser.add_argument(
        '-t', '--tcp', action="store_true",
        help="Run TCP traffic.")
    parser.add_argument(
        '-u', '--udp', action="store_true",
        help="Run UDP traffic.")
    parser.add_argument(
        '-x', '--http', action="store_true",
        help="Run HTTP traffic.")
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="Verbose mode")

    args = parser.parse_args()

    verbose = bool(args.verbose)

    Client, Server = None, None

    if args.tcp:
        Client, Server = hclient.TCPClient, hserver.TCPServer
    elif args.udp:
        Client, Server = hclient.UDPClient, hserver.UDPServer
    elif args.http:
        Client, Server = hclient.HTTPClient, hserver.HTTPServer

    assert(args.port)
    try:
        host = args.port[0]
        port = int(args.port[1])
    except Exception:
        _print("Invalid host/port")
        raise

    def ping_handler(payload, data, latency):
        if is_py3:
            try:
                payload = payload.decode()
                data = data.decode()
            except Exception:
                # HTTP Request handler might pass string itself.
                pass

        if payload == data:
            _print("Success : Sent: %s , received: %s, taken %s ms" % (payload, data, latency))
        else:
            _print("Failure : Sent: %s , received: %s, taken %s ms" % (payload, data, latency))

    ipv6 = args.ipv6

    _client, _server = None, None

    def signal_handler(sig, frame):
        if _client:
            _client.close()
            print ("\nClosed the client connection")
        if _server:
            _server.close()
            print ("\nClosed the server connection")

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(1)  # TODO : Fix it (for HTTP Protocol)

    signal.signal(signal.SIGINT, signal_handler)

    if args.server:
        ipv6 = args.ipv6
        _server = Server(port=port, verbose=verbose, ipv6=ipv6)
        _server.start()
    else:
        payload = args.load
        tries = args.num_pings or 5
        _client = Client(server=host, port=port, verbose=verbose,
                         handler=ping_handler, payload=payload,
                         tries=tries)
        _client.start()


if __name__ == '__main__':
    main()
