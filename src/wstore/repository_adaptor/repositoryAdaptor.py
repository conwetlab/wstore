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
import requests
import unicodedata
from urlparse import urljoin, urlsplit

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from wstore.store_commons.utils import mimeparser
from wstore.store_commons.errors import RepositoryError


def unreg_repository_adaptor_factory(url):
    adaptors = {
        'v1': RepositoryAdaptorV1,
        'v2': RepositoryAdaptorV2
    }

    split_path = urlsplit(url).path.split('/')

    if split_path[1] in adaptors:
        adaptor = adaptors[split_path[1]]
    elif split_path[2] in adaptors:
        adaptor = adaptors[split_path[2]]
    else:
        raise ObjectDoesNotExist('No RepositoryAdaptor has been found for the given URL')

    return adaptor(url)


def repository_adaptor_factory(repository, is_resource=False):

    adaptors = {
        1: RepositoryAdaptorV1,
        2: RepositoryAdaptorV2
    }

    collection = repository.resource_collection if is_resource else repository.offering_collection

    return adaptors[repository.api_version](repository.host, collection)


class RepositoryAdaptor(object):

    _repository_url = None
    _collection = None
    _credentials = None
    _asset_uri = None

    def __init__(self, repository_url, collection=None):

        self._repository_url = repository_url

        if collection is not None:
            if not self._repository_url.endswith('/'):
                self._repository_url += '/'

            self._collection = collection
            if not self._collection.endswith('/'):
                self._collection += '/'

    def set_credentials(self, credentials):
        self._credentials = credentials

    def set_uri(self, uri):
        self._asset_uri = uri

    def _build_url(self, name):
        url = self._repository_url

        if name is not None:
            name = name.replace(' ', '')
            url = urljoin(url, self._collection)
            url = urljoin(url, name)

        return url

    def _make_request(self, method, data, name, headers={}):
        url = self._build_url(name)

        if settings.OILAUTH:
            headers.update({'Authorization': 'Bearer ' + self._credentials})

        response = method(url, headers=headers, data=data.encode("utf-8"))

        if response.status_code < 200 or response.status_code >= 300:
            raise RepositoryError('The repository has failed processing the request')

        return response

    def download(self, name=None):

        response = self._make_request(requests.get, '', name, headers={'Accept': '*/*'})

        allowed_formats = ['text/plain', 'application/rdf+xml', 'text/turtle', 'text/n3']
        resp_content_type = mimeparser.best_match(allowed_formats, response.headers.get('content-type'))

        return {
            'content_type': resp_content_type,
            'data': response.text
        }

    def delete(self, name=None):
        self._make_request(requests.delete, '', name)


class RepositoryAdaptorV1(RepositoryAdaptor):

    def __init__(self, repository_url, collection=None):

        if collection is not None:
            repository_url = urljoin(repository_url, 'v1')

        super(RepositoryAdaptorV1, self).__init__(repository_url, collection=collection)

    def upload(self, content_type, data, name=None):

        # Only ASCII characters are allowed
        data = unicodedata.normalize('NFKD', data).encode('ascii', 'ignore')

        response = self._make_request(requests.put, data, name, headers={'Content-Type': content_type + '; charset=utf-8'})
        return response.url


class RepositoryAdaptorV2(RepositoryAdaptor):

    def __init__(self, repository_url, collection=None):

        if collection is not None:
            repository_url = urljoin(repository_url, 'v2/collec')

        super(RepositoryAdaptorV2, self).__init__(repository_url, collection=collection)

    def upload(self, content_type, data, name=None):
        # If a name has been provided, the resource is new
        if name is not None:
            # Create resource
            name = name.replace(' ', '-')

            content_url = self._asset_uri
            if self._asset_uri is None:
                content_url = self._build_url(name)

            res_meta = {
                'type': 'resource',
                'creator': settings.STORE_NAME,
                'name': name,
                'contentUrl': content_url,
                'contentFileName': name
            }
            self._make_request(requests.post, json.dumps(res_meta), '', headers={'Content-Type': 'application/json', 'Accept': 'application/json'})

        # Upload resource content
        response = self._make_request(requests.put, data, name, headers={'Content-Type': content_type})

        return response.url
