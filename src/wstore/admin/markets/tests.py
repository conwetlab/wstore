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
from urllib2 import HTTPError
from mock import MagicMock, call
from nose_parameterized import parameterized

from django.test import TestCase
from django.core.exceptions import PermissionDenied

from wstore.admin.markets import markets_management
from wstore.admin.markets import views
from wstore.store_commons.utils import http
from wstore.store_commons.utils.testing import decorator_mock, build_response_mock,\
    decorator_mock_callable, HTTPResponseMock


__test__ = False


BASIC_MARKET_DATA = {
    'name': 'test_market',
    'host': 'http://testmarket.com',
    'site': 'http://currentsite.com',
    'api_version': 1
}

BASIC_MARKET_DATA1 = {
    'name': 'test_market1',
    'host': 'http://testmarket.com/',
    'site': 'http://currentsite.com/',
    'api_version': 2
}


class RegisteringOnMarketplaceTestCase(TestCase):

    tags = ('fiware-ut-7',)

    @classmethod
    def setUpClass(cls):
        markets_management.settings = MagicMock()
        markets_management.settings.STORE_NAME = 'test_store'
        super(RegisteringOnMarketplaceTestCase, cls).setUpClass()

    def setUp(self):
        self.adaptor_object = MagicMock()
        markets_management.marketadaptor_factory = MagicMock()
        markets_management.marketadaptor_factory.return_value = self.adaptor_object

        markets_management.Marketplace = MagicMock()
        self._market_obj = MagicMock()
        markets_management.Marketplace.return_value = self._market_obj

        self.filter_mock = MagicMock()
        self.filter_mock.__len__.return_value = 0
        markets_management.Marketplace.objects.filter.return_value = self.filter_mock

    def _internal_market_error(self):
        self.adaptor_object.add_store.side_effect = HTTPError('site', 500, 'Internal server error', None, None)

    def _existing(self):
        self.filter_mock.__or__.return_value = ['m']

    def _creation_error(self):
        self._market_obj.save.side_effect = Exception('Creation error')

    @parameterized.expand([
        (BASIC_MARKET_DATA,),
        (BASIC_MARKET_DATA1, _internal_market_error, Exception, 'HTTP Error 500: Internal server error'),
        (BASIC_MARKET_DATA, _existing, PermissionDenied, 'Marketplace already registered'),
        (BASIC_MARKET_DATA, _creation_error, Exception, 'Creation error')
    ])
    def test_basic_registering_on_market(self, data, side_effect=None, err_type=None, err_msg=None):

        if side_effect:
            side_effect(self)

        error = None
        try:
            markets_management.register_on_market(data['name'], data['host'], data['api_version'], data['site'])
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)

            # Check calls
            markets_management.Marketplace.assert_called_with(
                name=data['name'],
                host='http://testmarket.com/',
                api_version=data['api_version']
            )

            markets_management.marketadaptor_factory.assert_called_with(self._market_obj)

            calls = [call(name=data['name']), call(host='http://testmarket.com/')]
            markets_management.Marketplace.objects.filter.assert_has_calls(calls)
            self.assertEquals(markets_management.Marketplace.objects.filter.call_count, 2)

            self.adaptor_object.add_store.assert_called_with({
                'store_name': 'test_store',
                'store_uri': data['site']
            })
            self._market_obj.save.assert_called_once_with()

        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


class MarketPlacesRetievingTestCase(TestCase):

    fixtures = ['get_mark.json']

    def test_basic_retrieving_of_markets(self):

        markets = markets_management.get_marketplaces()

        self.assertEquals(len(markets), 3)
        self.assertEquals(markets[0]['name'], 'test_market1')
        self.assertEquals(markets[0]['host'], 'http://examplemarketplace1.com/')
        self.assertEquals(markets[0]['api_version'], 1)
        self.assertEquals(markets[1]['name'], 'test_market2')
        self.assertEquals(markets[1]['host'], 'http://examplemarketplace2.com/')
        self.assertEquals(markets[1]['api_version'], 1)
        self.assertEquals(markets[2]['name'], 'test_market3')
        self.assertEquals(markets[2]['host'], 'http://examplemarketplace3.com/')
        self.assertEquals(markets[2]['api_version'], 2)


class UnregisteringFromMarketplaceTestCase(TestCase):

    tags = ('fiware-ut-8',)

    @classmethod
    def setUpClass(cls):
        markets_management.settings = MagicMock()
        markets_management.settings.STORE_NAME = 'test_store'
        super(UnregisteringFromMarketplaceTestCase, cls).setUpClass()

    def setUp(self):
        markets_management.Marketplace = MagicMock()
        self.adaptor_object = MagicMock()
        markets_management.marketadaptor_factory = MagicMock()
        markets_management.marketadaptor_factory.return_value = self.adaptor_object

    def _market_mock(self):
        mock_market = MagicMock()
        mock_market.host = 'http://testmarket.org/'
        markets_management.Marketplace.objects.get.return_value = mock_market

    def test_basic_unregistering_from_market(self):
        # Build the related Mock
        self._market_mock()
        markets_management.unregister_from_market('test_market')

        markets_management.Marketplace.objects.get.assert_called_with(name='test_market')
        self.adaptor_object.delete_store.assert_called_with('test_store')

    def test_unregistering_already_unregistered(self):

        self._market_mock()
        markets_management.Marketplace.objects.get.side_effect = Exception('Not found')
        error = False
        try:
            markets_management.unregister_from_market('test_market1')
        except:
            error = True

        self.assertTrue(error)

    def test_unregistering_bad_gateway(self):

        # Mock Marketplace
        self._market_mock()
        self.adaptor_object.delete_store.side_effect = HTTPError('http://testmarket.org', 500, 'Server error', None, None)

        error = False
        msg = None
        try:
            markets_management.unregister_from_market('test_market')
        except Exception as e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEquals(msg, 'Bad Gateway')
        self.adaptor_object.delete_store.assert_called_with('test_store')


class MarketplaceViewTestCase(TestCase):

    tags = ('market-view',)

    @classmethod
    def setUpClass(cls):
        # Mock class decorators
        http.authentication_required = decorator_mock
        http.supported_request_mime_types = decorator_mock_callable
        cls._old_http_response = views.HttpResponse

        reload(views)
        views.build_response = build_response_mock
        views.HttpResponse = HTTPResponseMock

        # Mock get_current_site methods
        views.get_current_site = MagicMock()
        site_obj = MagicMock()
        site_obj.domain = 'http://teststore.org'
        views.get_current_site.return_value = site_obj
        super(MarketplaceViewTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Restore mocked decorators
        views.HttpResponse = cls._old_http_response
        reload(http)
        reload(views)
        super(MarketplaceViewTestCase, cls).tearDownClass()

    def setUp(self):
        # Mock market management methods
        views.register_on_market = MagicMock()
        self.request = MagicMock()

    def _forbidden(self):
        self.request.user.is_staff = False

    def _market_failure(self):
        views.register_on_market.side_effect = HTTPError(
            'http://testmarket.com',
            500,
            'Internal server error',
            None,
            None
        )

    def _bad_request(self):
        views.register_on_market.side_effect = Exception('Bad request')

    def _existing(self):
        views.register_on_market.side_effect = PermissionDenied('Existing Marketplace')

    @parameterized.expand([
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (201, 'Created', 'correct'), False),
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (403, 'You are not allowed to register WStore in a Marketplace', 'error'), True, _forbidden),
        ({
            'invalid': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (400, 'Request body is not valid JSON data', 'error'), True),
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (502, 'The Marketplace has failed registering the store', 'error'), True, _market_failure),
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (500, 'Bad request', 'error'), True, _bad_request),
        ({
            'name': 'test_market$',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (400, 'Invalid name format', 'error'), True),
        ({
            'name': 'test_market',
            'host': 'invalid_url',
            'api_version': '1'
        }, (400, 'Invalid URL format', 'error'), True),
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1a'
        }, (400, 'Invalid API version', 'error'), True),
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '3'
        }, (400, 'Invalid API version', 'error'), True),
        ({
            'name': 'test_market',
            'host': 'http://testmarket.com',
            'api_version': '1'
        }, (403, 'Existing Marketplace', 'error'), True, _existing),
    ])
    def test_market_api_create(self, data, exp_resp, error, side_effect=None):
        # Create request data
        self.request.raw_post_data = json.dumps(data)

        if side_effect:
            side_effect(self)

        # Create the view
        market_collection = views.MarketplaceCollection(permitted_methods=('POST', 'GET'))

        response = market_collection.create(self.request)

        # Check response
        content = json.loads(response.content)
        self.assertEquals(response.status_code, exp_resp[0])
        self.assertEquals(content['message'], exp_resp[1])
        self.assertEquals(content['result'], exp_resp[2])

        # Check calls
        if not error:
            views.register_on_market.assert_called_with(data['name'], data['host'], int(data['api_version']), 'http://teststore.org')

    @parameterized.expand([
        (False,),
        (True,)
    ])
    def test_market_api_get(self, error):
        # Mock get marketplaces method
        views.get_marketplaces = MagicMock()

        # Create the view
        market_collection = views.MarketplaceCollection(permitted_methods=('GET', 'POST'))

        # Set return value for get_marketplaces
        data = None
        if not error:
            data = {
                'marketplaces': [{
                    'name': 'test_marketplace',
                    'host': 'http://testmarketplace.org'
                }]
            }
            views.get_marketplaces.return_value = data
        else:
            views.get_marketplaces.side_effect = Exception('Market error')

        # Call the marketplace view
        response = market_collection.read(self.request)

        # Check response
        if not error:
            self.assertEquals(response.status, 200)
            self.assertEquals(response.mimetype, 'application/JSON; charset=UTF-8')
            self.assertEquals(json.loads(response.data), data)
        else:
            content = json.loads(response.content)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(content['message'], 'Invalid request')
            self.assertEquals(content['result'], 'error')

    def _bad_gateway_unreg(self):
        views.unregister_from_market.side_effect = Exception('Bad Gateway')

    def _not_found_unreg(self):
        views.unregister_from_market.side_effect = Exception('Not found')

    def _market_failure_unreg(self):
        views.unregister_from_market.side_effect = Exception('Bad request')

    @parameterized.expand([
        ((204, 'No content', 'correct'),),
        ((403, 'Forbidden', 'error'), _forbidden),
        ((502, 'Bad Gateway', 'error'), _bad_gateway_unreg),
        ((404, 'Not found', 'error'), _not_found_unreg),
        ((400, 'Bad request', 'error'), _market_failure_unreg)
    ])
    def test_market_api_delete(self, exp_result, side_effect=None):
        # Mock unregister_form_market
        views.unregister_from_market = MagicMock()

        # Check if side effect
        if side_effect:
            side_effect(self)

        # Create the view
        market_entry = views.MarketplaceEntry(permitted_methods=('DELETE',))

        # Call the view
        response = market_entry.delete(self.request, 'test_market')

        # Check response
        content = json.loads(response.content)
        self.assertEquals(response.status_code, exp_result[0])
        self.assertEquals(content['message'], exp_result[1])
        self.assertEquals(content['result'], exp_result[2])
