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

from __future__ import unicode_literals

import json
import urllib2
from urllib2 import HTTPError

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.models import RSS


class RSSManager():

    _rss = None
    _credentials = None

    def __init__(self, rss, credentials):
        self._rss = rss
        self._credentials = credentials

    def _make_request(self, method, url, data={}):
        """
           Makes requests to the RSS
        """
        opener = urllib2.build_opener()

        headers = {
            'content-type': 'application/json',
            'X-Auth-Token': self._credentials
        }
        request = MethodRequest(method, url, json.dumps(data), headers)

        response = opener.open(request)    

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return response

    def _refresh_rss(self):
        self._rss = RSS.objects.get(name=self._rss.name)

    def set_credentials(self, credentials):
        self._credentials = credentials
