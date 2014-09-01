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

import SimpleHTTPServer
import threading
import SocketServer

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_PUT(self):
        self.path = '/'
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


class TestServer(threading.Thread):

    _keep_running = True
    _call_received = False

    def set_port(self, port):
        self.testing_port = port

    def stop_server(self):
        self._keep_running = False
        self.httpd.socket.close()

    def call_received(self):
        return self._call_received

    def run(self):
        Handler = ServerHandler
        self.httpd = SocketServer.TCPServer(("", self.testing_port), Handler)

        # A single request is handle
        self.httpd.handle_request()
        self._call_received = True
