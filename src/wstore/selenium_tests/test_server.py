# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.

import socket
import SimpleHTTPServer
import threading
import SocketServer

REQ_PATH = None
IGNORE = False


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    _req_path = None

    def __init__(self, request, client_address, server):
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_GET(self):
        global REQ_PATH
        if self.path != '/favicon.ico':
            REQ_PATH = self.path
        else:
            global IGNORE
            IGNORE = True

        self.path = '/'
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        global REQ_PATH
        REQ_PATH = self.path
        self.path = '/'
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_PUT(self):
        self.path = '/'
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


class TCPServerReuse(SocketServer.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


class TestServer(threading.Thread):

    _keep_running = True
    _calls_received = 0
    max_request = 0

    def set_port(self, port):
        self.testing_port = port

    def set_max_request(self, max_req):
        self.max_request = max_req

    def stop_server(self):
        self._keep_running = False
        self.httpd.socket.close()

    def call_received(self):
        return self._calls_received

    def get_path(self):
        global REQ_PATH
        return REQ_PATH

    def run(self):
        global IGNORE
        self.Handler = ServerHandler
        self.httpd = TCPServerReuse(("", self.testing_port), self.Handler)

        # A single request is handle
        while self._calls_received < self.max_request:
            self.httpd.handle_request()
            if not IGNORE:
                self._calls_received += 1

        self.httpd.socket.close()
