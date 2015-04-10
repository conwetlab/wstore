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

import urlparse
from urllib2 import HTTPError
from mock import MagicMock

from django.test import TestCase

from wstore.market_adaptor import marketadaptor


__test__ = False


class FakeUrllib2():

    _opener = None

    class Opener():

        _method = None
        _username = None
        _passwd = None
        _url = None
        _response = None

        def __init__(self, response):
            self._response = response

        def open(self, request):

            if request.get_host() == 'authentication_marketplace':
                self._url = request.get_full_url()
                self._method = request.get_method()
                data = request.get_data()
                self._username = urlparse.parse_qs(data)['j_username'][0]
                self._passwd = urlparse.parse_qs(data)['j_password'][0]
                return self._response

            elif request.get_host() == 'authentication_error':
                raise HTTPError(request.get_full_url(), 403, 'Error', None, None)

            elif request.get_host() == 'add_store_error':
                raise HTTPError(request.get_full_url(), 400, 'Error add store', None, None)

            elif request.get_host() == 'add_service_error':
                raise HTTPError(request.get_full_url(), 400, 'Error add service', None, None)

            elif request.get_host() == 'delete_store_error':
                raise HTTPError(request.get_full_url(), 400, 'Error delete store', None, None)

            elif request.get_host() == 'delete_service_error':
                raise HTTPError(request.get_full_url(), 400, 'Error delete service', None, None)

            elif request.get_host().endswith('redirection'):
                raise HTTPError(request.get_full_url(), 302, 'Redirection', None, None)

            elif request.get_host() == 'add_store_marketplace':
                self._url = request.get_full_url()
                self._method = request.get_method()
                self._body = request.data
                return self._response

            elif request.get_host() == 'add_service_marketplace':
                self._url = request.get_full_url()
                self._method = request.get_method()
                self._body = request.data
                return self._response

            elif request.get_host() == 'delete_store_marketplace':
                self._url = request.get_full_url()
                self._method = request.get_method()
                self._response.code = 200
                return self._response

            elif request.get_host() == 'delete_service_marketplace':
                self._url = request.get_full_url()
                self._method = request.get_method()
                self._response.code = 200
                return self._response

    class Response():
        url = 'http://response.com/v1/FiwareMarketplace;jsessionid=1111'
        code = 201

    def __init__(self):
        self._opener = self.Opener(self.Response())

    def build_opener(self):
        return self._opener


class MarketAdaptorTestCase(TestCase):

    tags = ('market-adaptor', )

    def setUp(self):
        self.fake_urllib = FakeUrllib2()
        marketadaptor.urllib2 = self.fake_urllib
        self.marketplace = MagicMock()
        self.marketplace.name = 'test_market'
        self.marketplace.api_version = 1

    def tearDown(self):
        reload(marketadaptor)

    def _get_marketadaptor(self, host):
        self.marketplace.host = host
        market_adaptor = marketadaptor.marketadaptor_factory(self.marketplace)
        market_adaptor._session_id = '1111'

        return market_adaptor

    def test_add_store_v1(self):
        expected_body = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="store" ><url>http://store_uri.com</url></resource>'

        store_info = {
            'store_name': 'store',
            'store_uri': 'http://store_uri.com'
        }

        market_adaptor = self._get_marketadaptor('http://add_store_marketplace/')

        market_adaptor.add_store(store_info)

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_store_marketplace/v1/registration/store/')
        self.assertEqual(opener._method, 'PUT')
        self.assertEqual(opener._body, expected_body)

    test_add_store_v1.tags = ('fiware-ut-7',)

    def test_add_store_error_v1(self):
        store_info = {
            'store_name': 'store',
            'store_uri': 'http://store_uri.com'
        }

        market_adaptor = self._get_marketadaptor('http://add_store_error/')

        error = False
        msg = None
        try:
            market_adaptor.add_store(store_info)
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error add store')

    test_add_store_error_v1.tags = ('fiware-ut-7',)

    def test_delete_store_v1(self):
        market_adaptor = self._get_marketadaptor('http://delete_store_marketplace/')

        market_adaptor.delete_store('test_store')

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://delete_store_marketplace/v1/registration/store/test_store')
        self.assertEqual(opener._method, 'DELETE')

    def test_delete_store_error_v1(self):
        market_adaptor = self._get_marketadaptor('http://delete_store_error/')

        error = False
        msg = None
        try:
            market_adaptor.delete_store('test_store')
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error delete store')

    def test_add_service_v1(self):
        expected_body = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="test_service" ><url>http://test_service_uri.com</url></resource>'

        service_info = {
            'name': 'test_service',
            'url': 'http://test_service_uri.com'
        }

        market_adaptor = self._get_marketadaptor('http://add_service_marketplace/')

        market_adaptor.add_service('test_store', service_info)

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_service_marketplace/v1/offering/store/test_store/offering')
        self.assertEqual(opener._method, 'PUT')
        self.assertEqual(opener._body, expected_body)

    test_add_service_v1.tags = ('fiware-ut-4',)

    def test_add_service_error_v1(self):
        service_info = {
            'name': 'test_service',
            'url': 'http://test_service_uri.com'
        }

        market_adaptor = self._get_marketadaptor('http://add_service_error/')

        error = False
        msg = None
        try:
            market_adaptor.add_service('test_store', service_info)
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error add service')

    test_add_service_error_v1.tags = ('fiware-ut-4',)

    def test_delete_service_v1(self):
        market_adaptor = self._get_marketadaptor('http://delete_service_marketplace/')

        market_adaptor.delete_service('test_store', 'test_service')

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://delete_service_marketplace/v1/offering/store/test_store/offering/test_service')
        self.assertEqual(opener._method, 'DELETE')

    test_delete_service_v1.tags = ('fiware-ut-9',)

    def test_delete_service_error_v1(self):
        market_adaptor = self._get_marketadaptor('http://delete_service_error/')

        error = False
        msg = None
        try:
            market_adaptor.delete_service('test_store', 'test_service')
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error delete service')

    test_delete_service_error_v1.tags = ('fiware-ut-9',)
