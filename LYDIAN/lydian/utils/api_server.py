#!/usr/bin/env python
# Copyright (c) 2020-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.

# Run: python3 api_server.py db_file port

import json
import re

from sys import argv
from urllib import parse
try:
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
except (ModuleNotFoundError, ImportError):
    # python 3.6 and before.
    import socketserver
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        pass

from sql30 import db
from sql30.api import SQL30Handler

DBPATH = None

class LydianApiHandler(SQL30Handler):

    def do_POST(self):
        self._set_headers()
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length).decode('utf-8')
        d = dict(parse.parse_qs(data))
        new_data = {key: value[0] for key, value in d.items()}

        if not self.path or self.path == '/':
            print("doing nothing")
        else:
            self._write_record(new_data)

    def _write_record(self, data):
        class DummyDB(db.Model):
            pass
        
        with DummyDB(db_name=DBPATH) as dummydb:
            dummydb.fetch_schema()
            path = self.path.split('/')
            tidx = path.index('tables')
            dummydb.table = path[tidx+1]
            dummydb.write(**data)


    # GET sends back a Hello world message
    def do_GET(self):
        self._set_headers()
        if not self.path or self.path == '/':
            response = json.dumps({'hello': 'world', 'received': 'ok'})
        elif re.match(r"/api/v1/endpoints/*/*", self.path):
            response = self._get_data()
        elif self.path == '/tables':
            response = self._get_tables()
        else:
            response = self._get_records()

        response = bytes(response, 'utf-8')
        self.wfile.write(response)

    def _get_data(self):
        class DummyDB(db.Model):
            pass

        with DummyDB(db_name=DBPATH) as dummydb:
            path_data = self.path.split('/')
            table_name = path_data[-1]
            endpoint_ip = path_data[-2]
            dummydb.fetch_schema()
            dummydb.table = table_name
            records = dummydb.read(include_header=True, host=endpoint_ip)
            header = records[0]
            data = records[1:]
            data_json = []
            for row in data:
                data_json.append(dict(zip(header, row)))
            return json.dumps(data_json)

    def _get_tables(self):
        class DummyDB(db.Model):
            pass

        with DummyDB(db_name=DBPATH) as dummydb:
            tables = dummydb.table_names
            return json.dumps(tables)

    def _get_records(self):
        class DummyDB(db.Model):
            pass

        with DummyDB(db_name=DBPATH) as dummydb:
            dummydb.fetch_schema()
            path = self.path.split('/')
            tidx = path.index('tables')
            dummydb.table = path[tidx+1]
            records = dummydb.read(include_header=True)
            header = records[0]
            data = records[1:]
            data_json = []
            for row in data:
                data_json.append(dict(zip(header, row)))
            return json.dumps(data_json)


def start_server(db_path, server=ThreadingHTTPServer, handler=LydianApiHandler, port=8008):
    global DBPATH
    DBPATH = db_path

    server_address = ('', port)
    httpd = server(server_address, handler)

    print('Starting httpd on port %d...' % port)
    httpd.serve_forever()


if __name__ == "__main__":
    if len(argv) >= 2:
        start_server(argv[1], port=int(argv[2]))
    else:
        start_server(None)
