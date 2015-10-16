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

import urlparse
from urllib2 import HTTPError
from mock import MagicMock
from nose_parameterized import parameterized

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

            elif request.get_host().startswith('delete_store_marketplace'):
                self._url = request.get_full_url()
                self._method = request.get_method()
                self._response.code = 200
                if request.get_host().endswith('v2'):
                    self._response.code = 204
                return self._response

            elif request.get_host().startswith('delete_service_marketplace'):
                self._url = request.get_full_url()
                self._method = request.get_method()
                self._response.code = 200
                if request.get_host().endswith('v2'):
                    self._response.code = 204
                return self._response

    class Response():
        def __init__(self):
            self.url = 'http://response.com/v1/FiwareMarketplace;jsessionid=1111'
            self.code = 201
            self.headers = MagicMock()
            self.headers.getheader.return_value = 'http://examplemarket.com/wstore'

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
        self.marketplace.store_id = 'test_store'
        self.marketplace.credentials.username = 'test_user'
        self.marketplace.credentials.passwd = 'testpasswd'

        marketadaptor.Marketplace = MagicMock()
        marketadaptor.Marketplace.objects.get.return_value = self.marketplace

        self.offering = MagicMock(name="Offering")
        self.offering.name = "test_service"
        self.offering.owner_organization.name = "test_org"
        self.offering.version = "1.0"
        self.offering.description_url = "http://test_service_uri.com"
        self.offering.get_uri.return_value = "http://offering_usdl_uri.org/"

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

    def _delete_store(self, market_url, expected_url):
        market_adaptor = self._get_marketadaptor(market_url)

        market_adaptor.delete_store()

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, expected_url)
        self.assertEqual(opener._method, 'DELETE')
        marketadaptor.Marketplace.objects.get.assert_called_once_with(host=market_url)

    def test_delete_store_v1(self):
        self._delete_store(
            'http://delete_store_marketplace',
            'http://delete_store_marketplace/v1/registration/store/test_store'
        )

    def test_delete_store_error_v1(self):
        market_adaptor = self._get_marketadaptor('http://delete_store_error/')

        error = False
        msg = None
        try:
            market_adaptor.delete_store()
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error delete store')

    def test_add_service_v1(self):
        expected_body = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="test_org test_service 1.0" ><url>http://test_service_uri.com</url></resource>'

        market_adaptor = self._get_marketadaptor('http://add_service_marketplace/')

        market_adaptor.add_service(self.offering)

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_service_marketplace/v1/offering/store/test_store/offering')
        self.assertEqual(opener._method, 'PUT')
        self.assertEqual(opener._body, expected_body)
        marketadaptor.Marketplace.objects.get.assert_called_once_with(host="http://add_service_marketplace/")

    test_add_service_v1.tags = ('fiware-ut-4',)

    def test_add_service_error_v1(self):

        market_adaptor = self._get_marketadaptor('http://add_service_error/')

        error = False
        msg = None
        try:
            market_adaptor.add_service(self.offering)
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error add service')

    test_add_service_error_v1.tags = ('fiware-ut-4',)

    def _delete_service(self, market_url, expected_url):
        market_adaptor = self._get_marketadaptor(market_url)

        market_adaptor.delete_service('test_service')

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, expected_url)
        self.assertEqual(opener._method, 'DELETE')
        marketadaptor.Marketplace.objects.get.assert_called_once_with(host=market_url)

    def test_delete_service_v1(self):
        self._delete_service(
            'http://delete_service_marketplace',
            'http://delete_service_marketplace/v1/offering/store/test_store/offering/test_service'
        )

    test_delete_service_v1.tags = ('fiware-ut-9',)

    def test_delete_service_error_v1(self):
        market_adaptor = self._get_marketadaptor('http://delete_service_error/')

        error = False
        msg = None
        try:
            market_adaptor.delete_service('test_service')
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error delete service')

    test_delete_service_error_v1.tags = ('fiware-ut-9',)

    def test_add_store_v2(self):
        self.marketplace.api_version = 2
        market_adaptor = self._get_marketadaptor('http://add_store_marketplace/')

        expected_body = {
            "displayName": "store",
            "url": "http://store_uri.com",
            "comment": "WStore instance deployed in http://store_uri.com"
        }

        store_info = {
            'store_name': 'store',
            'store_uri': 'http://store_uri.com'
        }

        market_adaptor = self._get_marketadaptor('http://add_store_marketplace/')

        store_id = market_adaptor.add_store(store_info)

        self.assertEquals(store_id, 'wstore')

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_store_marketplace/api/v2/store')
        self.assertEqual(opener._method, 'POST')
        self.assertEqual(json.loads(opener._body), expected_body)

    def test_delete_store_v2(self):
        self.marketplace.api_version = 2
        self._delete_store(
            'http://delete_store_marketplace_v2',
            'http://delete_store_marketplace_v2/api/v2/store/test_store'
        )

    def _set_v2_repo_url(self):
        self.offering.description_url = "http://test_service_uri.com/v2/collec/collection/test_service"

    def _set_v2_repo_url_app(self):
        self.offering.description_url = "http://test_service_uri.com/repo/v2/collec/collection/test_service"

    @parameterized.expand([
        ("repo_v1", {
            "displayName": "test_org test_service 1.0",
            "url": "http://test_service_uri.com",
        }),
        ("repo_v2_no_webapp", {
            "displayName": "test_org test_service 1.0",
            "url": 'http://test_service_uri.com/v2/services/query?query=CONSTRUCT+%7B+%3Fa+%3Fb+%3Fc+.+%3Fd+%3Fe+%3Ff+.+%7D+WHERE+%7B+%7B+GRAPH+%3Chttp%3A%2F%2Foffering_usdl_uri.org%2F%3E+%7B+%3Fa+%3Fb+%3Fc+%7D+%7D+UNION+%7B+%3Chttp%3A%2F%2Foffering_usdl_uri.org%2F%3E+%3Chttp%3A%2F%2Fwww.linked-usdl.org%2Fns%2Fusdl-core%23includes%3E+%3Fn+.+GRAPH+%3Fn+%7B+%3Fd+%3Fe+%3Ff+%7D+%7D%7D'
        }, _set_v2_repo_url),
        ("repo_v2", {
            "displayName": "test_org test_service 1.0",
            "url": 'http://test_service_uri.com/repo/v2/services/query?query=CONSTRUCT+%7B+%3Fa+%3Fb+%3Fc+.+%3Fd+%3Fe+%3Ff+.+%7D+WHERE+%7B+%7B+GRAPH+%3Chttp%3A%2F%2Foffering_usdl_uri.org%2F%3E+%7B+%3Fa+%3Fb+%3Fc+%7D+%7D+UNION+%7B+%3Chttp%3A%2F%2Foffering_usdl_uri.org%2F%3E+%3Chttp%3A%2F%2Fwww.linked-usdl.org%2Fns%2Fusdl-core%23includes%3E+%3Fn+.+GRAPH+%3Fn+%7B+%3Fd+%3Fe+%3Ff+%7D+%7D%7D',
        }, _set_v2_repo_url_app)
    ])
    def test_add_service_v2(self, name, expected_body, side_effect=None):

        self.marketplace.api_version = 2
        market_adaptor = self._get_marketadaptor('http://add_service_marketplace/')
        market_adaptor._user = None
        market_adaptor._current_user = MagicMock()
        market_adaptor._current_user.userprofile.access_token = 'access_token'

        if side_effect is not None:
            side_effect(self)

        store_id = market_adaptor.add_service(self.offering)

        self.assertEquals(store_id, 'wstore')

        opener = self.fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_service_marketplace/api/v2/store/test_store/description')
        self.assertEqual(opener._method, 'POST')
        self.assertEqual(json.loads(opener._body), expected_body)

    def test_delete_service_v2(self):
        self.marketplace.api_version = 2
        self._delete_service(
            'http://delete_service_marketplace_v2',
            'http://delete_service_marketplace_v2/api/v2/store/test_store/description/test_service'
        )
