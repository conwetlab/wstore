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

import urlparse
from urllib2 import HTTPError
from django.test import TestCase

from wstore.market_adaptor import marketadaptor


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

    def authentication(self):
            raise Exception('Redirection')

    def test_authentication(self):

        marketplace = 'http://authentication_marketplace/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace, user='test_user', passwd='test_passwd')

        market_adaptor.authenticate()

        opener = fake_urllib._opener
        self.assertEqual(opener._url, 'http://authentication_marketplace/FiwareMarketplace/j_spring_security_check')
        self.assertEqual(opener._method, 'POST')
        self.assertEqual(opener._username, 'test_user')
        self.assertEqual(opener._passwd, 'test_passwd')

        self.assertEqual(market_adaptor._session_id, '1111')

    def test_authentcation_error(self):

        marketplace = 'http://authentication_error/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace, user='test_user', passwd='test_passwd')

        error = False
        msg = None
        try:
            market_adaptor.authenticate()
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Marketplace login error')

    def test_add_store(self):
        expected_body = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="store" ><url>http://store_uri.com</url></resource>'

        store_info = {
            'store_name': 'store',
            'store_uri': 'http://store_uri.com'
        }

        marketplace = 'http://add_store_marketplace/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.add_store(store_info)

        opener = fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_store_marketplace/registration/store/')
        self.assertEqual(opener._method, 'PUT')
        self.assertEqual(opener._body, expected_body)

    def test_add_store_error(self):
        marketplace = 'http://add_store_error/'

        store_info = {
            'store_name': 'store',
            'store_uri': 'http://store_uri.com'
        }

        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        error = False
        msg = None
        try:
            market_adaptor.add_store(store_info)
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error add store')

    def test_add_store_redirection(self):
        marketplace = 'http://add_store_redirection/'

        store_info = {
            'store_name': 'store',
            'store_uri': 'http://store_uri.com'
        }

        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.authenticate = self.authentication
        redirected = False
        try:
            market_adaptor.add_store(store_info)
        except Exception, e:
            if e.message == 'Redirection':
                redirected = True

        self.assertTrue(redirected)

    def test_delete_store(self):
        marketplace = 'http://delete_store_marketplace/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.delete_store('test_store')

        opener = fake_urllib._opener
        self.assertEqual(opener._url, 'http://delete_store_marketplace/registration/store/test_store')
        self.assertEqual(opener._method, 'DELETE')

    def test_delete_store_error(self):

        marketplace = 'http://delete_store_error/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        error = False
        msg = None
        try:
            market_adaptor.delete_store('test_store')
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error delete store')

    def test_delete_store_redirection(self):

        marketplace = 'http://delete_store_redirection/'

        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.authenticate = self.authentication
        redirected = False
        try:
            market_adaptor.delete_store('test_store')
        except Exception, e:
            if e.message == 'Redirection':
                redirected = True

        self.assertTrue(redirected)

    def test_add_service(self):
        expected_body = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="test_service" ><url>http://test_service_uri.com</url></resource>'

        service_info = {
            'name': 'test_service',
            'url': 'http://test_service_uri.com'
        }

        marketplace = 'http://add_service_marketplace/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.add_service('test_store', service_info)

        opener = fake_urllib._opener
        self.assertEqual(opener._url, 'http://add_service_marketplace/offering/store/test_store/offering')
        self.assertEqual(opener._method, 'PUT')
        self.assertEqual(opener._body, expected_body)

    def test_add_service_error(self):

        marketplace = 'http://add_service_error/'

        service_info = {
            'name': 'test_service',
            'url': 'http://test_service_uri.com'
        }

        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        error = False
        msg = None
        try:
            market_adaptor.add_service('test_store', service_info)
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error add service')

    def test_add_service_redirection(self):

        marketplace = 'http://add_service_redirection/'

        service_info = {
            'name': 'test_service',
            'url': 'http://test_service_uri.com'
        }

        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.authenticate = self.authentication
        redirected = False
        try:
            market_adaptor.add_service('test_store', service_info)
        except Exception, e:
            if e.message == 'Redirection':
                redirected = True

        self.assertTrue(redirected)

    def test_delete_service(self):

        marketplace = 'http://delete_service_marketplace/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.delete_service('test_store', 'test_service')

        opener = fake_urllib._opener
        self.assertEqual(opener._url, 'http://delete_service_marketplace/offering/store/test_store/offering/test_service')
        self.assertEqual(opener._method, 'DELETE')

    def test_delete_service_error(self):

        marketplace = 'http://delete_service_error/'
        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        error = False
        msg = None
        try:
            market_adaptor.delete_service('test_store', 'test_service')
        except HTTPError, e:
            error = True
            msg = str(e.reason)

        self.assertTrue(error)
        self.assertEqual(msg, 'Error delete service')

    def test_delete_service_redirection(self):
        marketplace = 'http://delete_service_redirection/'

        fake_urllib = FakeUrllib2()

        marketadaptor.urllib2 = fake_urllib
        market_adaptor = marketadaptor.MarketAdaptor(marketplace)
        market_adaptor._session_id = '1111'

        market_adaptor.authenticate = self.authentication
        redirected = False
        try:
            market_adaptor.delete_service('test_store', 'test_service')
        except Exception, e:
            if e.message == 'Redirection':
                redirected = True

        self.assertTrue(redirected)
