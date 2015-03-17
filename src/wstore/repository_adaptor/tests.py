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

from urllib2 import HTTPError
from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.repository_adaptor import repositoryAdaptor


class RepositoryAdaptorTestCase(TestCase):

    tags = ('repository-adaptor', )

    def setUp(self):
        # Create mocks
        repositoryAdaptor.urllib2 = MagicMock(name="urllib2")
        self.opener_mock = MagicMock()

        self.response = MagicMock()
        self.response.code = 200
        self.response.headers = {
            'content-type': 'application/rdf+xml'
        }
        self.response.read.return_value = 'value returned'

        self.opener_mock.open.return_value = self.response
        repositoryAdaptor.urllib2.build_opener.return_value = self.opener_mock

        repositoryAdaptor.MethodRequest = MagicMock(name="MethodRequest")
        self.request = MagicMock()
        repositoryAdaptor.MethodRequest.return_value = self.request

    def tearDown(self):
        reload(repositoryAdaptor)

    def _http_error(self):
        self.opener_mock.open.side_effect = HTTPError('http://repository.com', 500, 'Internal error', None, None)

    def _error_code(self):
        self.response.code = 404

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
            self.assertTrue(isinstance(error, repositoryAdaptor.RepositoryError))
            self.assertEquals(unicode(e), err_msg)

    def _check_upload_response(self, rep_url, expected_url, content_type, data):
        # Check returned url
        self.assertEquals(rep_url, expected_url)

        # Check calls
        headers = {'content-type': content_type + '; charset=utf-8'}
        repositoryAdaptor.MethodRequest.assert_called_once_with('PUT', expected_url, data, headers)
        self.opener_mock.open.assert_called_once_with(self.request)

    @parameterized.expand([
        ('basic', 'application/rdf+xml', 'content',
            'http://repository.com/', 'http://repository.com/collection/resource', 'collection/', 'resource'),
        ('absolute_url', 'text/turtle', 'turtle content',
            'http://repository.com/resource', 'http://repository.com/resource'),
        ('http_error', 'application/rdf+xml', 'content', None, None, None, None, _http_error, 'Repository error: The repository has failed while uploading the resource'),
        ('error_code', 'application/rdf+xml', 'content', None, None, None, None, _error_code, 'Repository error: The repository has failed while uploading the resource')
    ])
    def test_upload(self, name, content_type, data, url, expected_url, collection=None, res_name=None, side_effect=None, err_msg=None):
        # Build repository adaptor object
        repository_adaptor = repositoryAdaptor.RepositoryAdaptor(url, collection)

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

        headers = {'Accept': '*'}
        repositoryAdaptor.MethodRequest.assert_called_once_with('GET', complete_url, '', headers)
        self.opener_mock.open.assert_called_once_with(self.request)

    @parameterized.expand([
        ('basic', 'http://repository.com', 'http://repository.com/collection/resource', 'collection', 'resource'),
        ('absolute_url', 'http://repository.com/collection/resource', 'http://repository.com/collection/resource'),
        ('http_error', 'http://repository.com/collection/resource', None, None, None, _http_error, 'Repository error: The repository has failed downloading the resource'),
        ('error_code', 'http://repository.com/collection/resource', None, None, None, _error_code, 'Repository error: The repository has failed downloading the resource')
    ])
    def test_download(self, name, url, complete_url, collection=None, res_name=None, side_effect=None, err_msg=None):
        # Build repository adaptor object
        repository_adaptor = repositoryAdaptor.RepositoryAdaptor(url, collection)

        self._execute_test(
            repository_adaptor.download,
            (res_name, ),
            self._check_download_response,
            (complete_url, ),
            side_effect,
            err_msg
        )

    def _check_delete_response(self, data, complete_url):
        repositoryAdaptor.MethodRequest.assert_called_once_with('DELETE', complete_url)
        self.opener_mock.open.assert_called_once_with(self.request)

    @parameterized.expand([
        ('basic', 'http://repository.com', 'http://repository.com/collection/resource', 'collection', 'resource'),
        ('absolute_url', 'http://repository.com/collection/resource', 'http://repository.com/collection/resource'),
        ('http_error', 'http://repository.com/collection/resource', None, None, None, _http_error, 'Repository error: The repository has failed deleting the resource'),
        ('error_code', 'http://repository.com/collection/resource', None, None, None, _error_code, 'Repository error: The repository has failed deleting the resource')
    ])
    def test_delete(self, name, url, complete_url, collection=None, res_name=None, side_effect=None, err_msg=None):

        repository_adaptor = repositoryAdaptor.RepositoryAdaptor(url, collection)

        self._execute_test(
            repository_adaptor.delete,
            (res_name, ),
            self._check_delete_response,
            (complete_url, ),
            side_effect,
            err_msg
        )
