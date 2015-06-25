# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.repository_adaptor import repositoryAdaptor
from wstore.store_commons.errors import RepositoryError


def _build_mock_request(method):
    status_values = {
        'get': 200,
        'put': 200,
        'post': 201,
        'delete': 204
    }

    # Build response
    response = MagicMock()
    response.status_code = status_values[method]

    if method == 'get':
        response.headers = {
            'content-type': 'application/rdf+xml'
        }
        response.text = 'value returned'

    def _mock_request(url, headers={}, data=''):
        # Check headers
        if 'Authorization' not in headers:
            response.status_code = 401

        if method == 'get' and 'Accept' not in headers:
            response.status_code = 406

        if (method == 'put' or method == 'post') and 'Content-Type' not in headers:
            response.status_code = 415

        response.url = url
        return response

    return _mock_request


class RepositoryAdaptorTestCase(TestCase):

    tags = ('repository-adaptor', )

    _repository_v1 = MagicMock()
    _repository_v2 = MagicMock()

    def setUp(self):
        # Create mocks
        repositoryAdaptor.requests = MagicMock(name="requests")

        repositoryAdaptor.requests.get = _build_mock_request('get')
        repositoryAdaptor.requests.put = _build_mock_request('put')
        repositoryAdaptor.requests.post = _build_mock_request('post')
        repositoryAdaptor.requests.delete = _build_mock_request('delete')

        # Mpck repository objects
        self._repository_v1.name = 'TestRepository1'
        self._repository_v1.host = 'http://testrepo1.com/'
        self._repository_v1.api_version = 1
        self._repository_v1.offering_collection = 'testOfferingCollectionv1'
        self._repository_v1.resource_collection = 'testResourceCollectionv1'

        self._repository_v2.name = 'TestRepository2'
        self._repository_v2.host = 'http://testrepo2.com/'
        self._repository_v2.api_version = 2
        self._repository_v2.offering_collection = 'testOfferingCollectionv2'
        self._repository_v2.resource_collection = 'testResourceCollectionv2'

    def tearDown(self):
        reload(repositoryAdaptor)

    def _error_code(self):
        response = MagicMock()
        response.status_code = 500
        repositoryAdaptor.requests = MagicMock()
        repositoryAdaptor.requests.get.return_value = response
        repositoryAdaptor.requests.put.return_value = response
        repositoryAdaptor.requests.post.return_value = response
        repositoryAdaptor.requests.delete.return_value = response

    def _execute_test(self, method, args, checker, expected_data, side_effect=None, err_msg=None):

        if side_effect is not None:
            side_effect(self)

        error = None
        try:
            response = method(*args)
        except Exception as e:
            error = e

        if err_msg is None:
            self.assertTrue(error is None)
            # Call specific checker
            checker(response, *expected_data)
        else:
            self.assertTrue(isinstance(error, RepositoryError))
            self.assertEquals(unicode(e), err_msg)

    def _check_upload_response(self, rep_url, expected_url, content_type, data):
        # Check returned url
        self.assertEquals(rep_url, expected_url)

    @parameterized.expand([
        ('basic_v1', 'application/rdf+xml', 'content', _repository_v1,
            'http://testrepo1.com/v1/testOfferingCollectionv1/resource', 'resource'),
        ('basic_v2', 'application/rdf+xml', 'content', _repository_v2,
            'http://testrepo2.com/v2/collec/testOfferingCollectionv2/resource', 'resource'),
        ('resource', 'application/rdf+xml', 'content', _repository_v2,
            'http://testrepo2.com/v2/collec/testResourceCollectionv2/resource', 'resource', True),
        ('error_v1', 'application/rdf+xml', 'content', _repository_v1, None, None, False, _error_code, 'The repository has failed processing the request'),
        ('error_v2', 'application/rdf+xml', 'content', _repository_v2, None, None, False, _error_code, 'The repository has failed processing the request')
    ])
    def test_upload(self, name, content_type, data, repository, expected_url, res_name=None, is_resource=False, side_effect=None, err_msg=None):
        # Build repository adaptor object
        repository_adaptor = repositoryAdaptor.repository_adaptor_factory(repository, is_resource=is_resource)
        repository_adaptor.set_credentials('11111')

        # Execute test
        self._execute_test(
            repository_adaptor.upload,
            (content_type, data, res_name),
            self._check_upload_response,
            (expected_url, content_type, data),
            side_effect,
            err_msg
        )

    def _check_download_response(self, data, complete_url):
        self.assertEquals(data, {
            'content_type': 'application/rdf+xml',
            'data': 'value returned'
        })

    @parameterized.expand([
        ('basic_v1', 'http://repository.com/v1/collection/resource'),
        ('basic_v2', 'http://repository.com/v2/collec/collection/resource'),
        ('error_code_v1', 'http://repository.com/v1/collection/resource', _error_code, 'The repository has failed processing the request'),
        ('error_code_v2', 'http://repository.com/v2/collec/collection/resource', _error_code, 'The repository has failed processing the request')
    ])
    def test_download(self, name, url, side_effect=None, err_msg=None):
        # Build repository adaptor object
        repository_adaptor = repositoryAdaptor.unreg_repository_adaptor_factory(url)
        repository_adaptor.set_credentials('11111')

        self._execute_test(
            repository_adaptor.download,
            (None,),
            self._check_download_response,
            (url, ),
            side_effect,
            err_msg
        )

    def _check_delete_response(self, data, complete_url):
        pass

    @parameterized.expand([
        ('basic_v1', 'http://repository.com/v1/collection/resource'),
        ('basic_v2', 'http://repository.com/v2/collec/collection/resource'),
        ('error_code_v1', 'http://repository.com/v1/collection/resource', _error_code, 'The repository has failed processing the request'),
        ('error_code_v2', 'http://repository.com/v2/collec/collection/resource', _error_code, 'The repository has failed processing the request')
    ])
    def test_delete(self, name, url, side_effect=None, err_msg=None):
        repository_adaptor = repositoryAdaptor.unreg_repository_adaptor_factory(url)
        repository_adaptor.set_credentials('11111')

        self._execute_test(
            repository_adaptor.delete,
            (None, ),
            self._check_delete_response,
            (url, ),
            side_effect,
            err_msg
        )
