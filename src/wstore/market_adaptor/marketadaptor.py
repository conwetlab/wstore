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

import urllib2
from urllib2 import HTTPError
from urllib import urlencode
from urlparse import urljoin, urlparse
from base64 import b64encode

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.store_commons.utils.url import url_fix


def marketadaptor_factory(marketplace):
    """
    Returns the corresponding MarketAdaptor depending on the API version
    """

    adaptors = {
        1: MarketAdaptorV1,
        2: MarketAdaptorV2
    }

    return adaptors[marketplace.api_version](marketplace.host)


class MarketAdaptor():

    def __init__(self, marketplace_uri, user='store_conwet', passwd='store_conwet'):
        self._marketplace_uri = marketplace_uri
        self._user = user
        self._passwd = passwd

    def add_store(self, store_info):
        pass

    def delete_store(self, store):
        pass

    def add_service(self, store, service_info):
        pass

    def delete_service(self, store, service):
        pass


class MarketAdaptorV1(MarketAdaptor):

    _marketplace_uri = None

    def _make_request(self, method, url, params, headers, code):
        opener = urllib2.build_opener()

        # Include credentials in the header
        token = b64encode(self._user + ':' + self._passwd)
        headers['Authorization'] = 'Basic ' + token

        request = MethodRequest(method, url, params, headers)
        response = opener.open(request)

        if response.code != code:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def add_store(self, store_info):

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + store_info['store_name'] + '" ><url>' + store_info['store_uri'] + '</url></resource>'
        headers = {'content-type': 'application/xml'}

        url = urljoin(self._marketplace_uri, "v1/registration/store/")
        self._make_request('PUT', url, params, headers, 201)

    def delete_store(self, store):

        url = urljoin(self._marketplace_uri, "v1/registration/store/" + store)

        url = url_fix(url)
        self._make_request('DELETE', url, '', {}, 200)

    def add_service(self, store, service_info):

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + service_info['name'] + '" ><url>' + service_info['url'] + '</url></resource>'
        headers = {'content-type': 'application/xml'}
        url = urljoin(self._marketplace_uri, "v1/offering/store/" + store + "/offering")

        url = url_fix(url)
        self._make_request('PUT', url, params, headers, 201)

    def delete_service(self, store, service):

        url = urljoin(self._marketplace_uri, "v1/offering/store/" + store + "/offering/" + service)
        url = url_fix(url)

        self._make_request('DELETE', url, '', {}, 200)


class MarketAdaptorV2(MarketAdaptor):

    def add_store(self, store_info):

        opener = urllib2.build_opener()
        headers = {
            'Content-type': 'application/json'
        }
