# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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
from urlparse import urljoin

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.models import RSS


class RSSManager(object):

    _rss = None
    _credentials = None

    def __init__(self, rss, credentials):
        self._rss = rss
        self._credentials = credentials

    def _get_auth_header(self):
        return 'X-Auth-Token'

    def _get_token_type(self):
        return ""

    def _make_request(self, method, url, data={}):
        """
           Makes requests to the RSS
        """
        opener = urllib2.build_opener()

        auth_header = self._get_auth_header()

        headers = {
            'content-type': 'application/json'
        }

        headers[auth_header] = self._get_token_type() + self._credentials

        request = MethodRequest(method, url, json.dumps(data), headers)

        response = opener.open(request)

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return response

    def _refresh_rss(self):
        self._rss = RSS.objects.get(name=self._rss.name)

    def set_credentials(self, credentials):
        self._credentials = credentials


class ProviderManager(RSSManager):

    def _get_auth_header(self):
        return 'Authorization'

    def _get_token_type(self):
        return "Bearer "

    def register_provider(self, provider_info):
        """
        Register a new provider in the RSS v2
        """
        data = {
            'aggregatorId': self._rss.aggregator_id,
            'providerId': provider_info['provider_id'],
            'providerName': provider_info['provider_name']
        }

        endpoint = urljoin(self._rss.host, 'fiware-rss/rss/providers')
        self._make_request('POST', endpoint, data)
