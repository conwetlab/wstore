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

import urllib2
from urllib2 import HTTPError
from urlparse import urljoin

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.store_commons.utils import mimeparser


class RepositoryAdaptor():

    _repository_url = None
    _collection = None

    def __init__(self, repository_url, collection=None):

        self._repository_url = repository_url

        if not self._repository_url.endswith('/'):
            self._repository_url += '/'

        if collection != None:
            self._collection = collection
            if not self._collection.endswith('/'):
                self._collection += '/'

    def upload(self, content_type, data, name=None):

        opener = urllib2.build_opener()
        url = self._repository_url

        if name != None:
            name = name.replace(' ', '')
            url = urljoin(self._repository_url, self._collection)
            url = urljoin(url, name)

        headers = {'content-type': content_type + '; charset=utf-8'}
        request = MethodRequest('PUT', url, data.encode('utf-8'), headers)

        request.data = ''.join([i if ord(i) < 128 else ' ' for i in request.data])
        response = opener.open(request)

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return url

    def download(self, name=None, content_type='application/rdf+xml'):

        url = self._repository_url
        opener = urllib2.build_opener()

        if name != None:
            name = name.replace(' ', '')
            url = urljoin(url, self._collection)
            url = urljoin(url, name)

        headers = {'Accept': '*'}
        request = MethodRequest('GET', url, '', headers)

        response = opener.open(request)

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)

        allowed_formats = ['text/plain', 'application/rdf+xml', 'text/turtle', 'text/n3']
        resp_content_type = mimeparser.best_match(allowed_formats, response.headers.get('content-type'))

        return {
            'content_type': resp_content_type,
            'data': response.read()
        }

    def delete(self, name=None):

        opener = urllib2.build_opener()
        url = self._repository_url

        if name != None:
            name = name.replace(' ', '')
            url = urljoin(self._repository_url, self._collection)
            url = urljoin(url, name)

        request = MethodRequest('DELETE', url)

        response = opener.open(request)

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)
