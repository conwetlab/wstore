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

import json
import types
from mock import MagicMock
from nose_parameterized import parameterized
from urllib2 import HTTPError

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from wstore.admin.organizations import views
from wstore.models import Organization
from wstore.store_commons.utils.testing import decorator_mock, build_response_mock,\
decorator_mock_callable
from wstore.admin.rss.tests import ExpenditureMock


class OrganizationChangeTestCase(TestCase):

    tags = ('fiware-ut-25',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        # Create testing request
        self.data = {
            'organization': 'test_org'
        }
        self.request = self.factory.put(
            '/administration/organizations/change',
            json.dumps(self.data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.request.user = self.user

    def test_organization_change(self):

        org = Organization.objects.create(
            name='test_org'
        )
        # Update user profile info
        self.user.userprofile.organizations.append({
            'organization': org.pk
        })
        self.user.userprofile.save()

        response = views.change_current_organization(self.request)
        self.user = User.objects.get(username='test_user')
        self.assertEquals(self.user.userprofile.current_organization.pk, org.pk)

        body_response = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(body_response['message'], 'OK')
        self.assertEquals(body_response['result'], 'correct')

    def test_organization_change_errors(self):

        errors = [
            'Not found',
            'Forbidden'
        ]
        for i in [0, 1]:
            if i == 1:
                Organization.objects.create(
                    name='test_org'
                )

            response = views.change_current_organization(self.request)

            body_response = json.loads(response.content)
            self.assertEquals(body_response['message'], errors[i])
            self.assertEquals(body_response['result'], 'error')


class OrganizationEntryTestCase(TestCase):

    tags = ('org-admin',)

    @classmethod
    def setUpClass(cls):
        from wstore.store_commons.utils import http
        # Save the reference of the decorators
        cls._old_auth = types.FunctionType(
            http.authentication_required.func_code,
            http.authentication_required.func_globals,
            name=http.authentication_required.func_name,
            argdefs=http.authentication_required.func_defaults,
            closure=http.authentication_required.func_closure
        )

        cls._old_supp = types.FunctionType(
            http.supported_request_mime_types.func_code,
            http.supported_request_mime_types.func_globals,
            name=http.supported_request_mime_types.func_name,
            argdefs=http.supported_request_mime_types.func_defaults,
            closure=http.supported_request_mime_types.func_closure
        )

        # Mock class decorators
        http.authentication_required = decorator_mock
        http.supported_request_mime_types = decorator_mock_callable

        reload(views)
        views.build_response = build_response_mock
        views.RSS = MagicMock()
        rss_object = MagicMock()
        views.RSS.objects.all.return_value = [rss_object]
        views.ExpenditureManager = MagicMock()

        views._check_limits = MagicMock()
        views._check_limits.return_value = {
            'currency': 'EUR',
            'perTransaction': '100',
            'weekly': '150'
        }
        super(OrganizationEntryTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Restore mocked decorators
        from wstore.store_commons.utils import http
        http.authentication_required = cls._old_auth
        http.supported_request_mime_types = cls._old_supp
        super(OrganizationEntryTestCase, cls).tearDownClass()

    def setUp(self):
        # Create request user mock
        user_object = MagicMock()
        user_object.username = 'test_user'
        user_object.pk = '1111'
        user_object.is_staff = False
        self.request = MagicMock()
        self.request.user = user_object

        # Create organization mock
        self.org_object = MagicMock()
        self.org_object.name = 'test_org'
        self.org_object.managers = ['1111']
        self.org_object.payment_info = {
            'number': '4567456745674567'
        }
        views.Organization = MagicMock()
        views.Organization.objects.get.return_value = self.org_object

    def _mock_expenditure_401(self):
        exp_mock = ExpenditureMock()
        views.ExpenditureManager = exp_mock.ExpenditureManager

    def _not_found(self):
        views.Organization.objects.get.side_effect = Exception('')

    def _forbidden(self):
        self.org_object.managers = []

    def _unauthorized(self):
        views.ExpenditureManager = MagicMock()
        exp_object = MagicMock()
        exp_object.set_actor_limit.side_effect = HTTPError('http://rss.test.com', 401, 'Unauthorized', None, None)
        views.ExpenditureManager.return_value = exp_object

    def _rss_failure(self):
        views.ExpenditureManager = MagicMock()
        exp_object = MagicMock()
        exp_object.set_actor_limit.side_effect = HTTPError('http://rss.test.com', 500, 'Server error', None, None)
        views.ExpenditureManager.return_value = exp_object

    @parameterized.expand([
    ({
        'notification_url': 'http://notificationurl.com',
        'tax_address': {
            'street': 'fake street 123',
            'country': 'Country',
            'city': 'City',
            'postal': '12345'
        },
        'payment_info': {
            'number': '1234123412341234',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        },
        'limits': {
            'perTransaction': '100',
            'weekly': '150'
        }
    }, (200, 'OK', 'correct'), False),
    ({
        'payment_info': {
            'number': 'xxxxxxxxxxxx4567',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        },
        'limits': {
            'perTransaction': '100',
            'weekly': '150'
        }
    }, (200, 'OK', 'correct'), False, _mock_expenditure_401),
    ({}, (200, 'OK', 'correct'), False),
    ({}, (404, 'Not found', 'error'), True, _not_found),
    ({}, (403, 'Forbidden', 'error'), True, _forbidden),
    ({
        'notification_url': 'invalidurl'
    }, (400, 'Invalid notification URL', 'error'), True),
    ({
        'limits': {
            'perTransaction': '100',
            'weekly': '150'
        }
    }, (400, 'Invalid content', 'error'), True, _unauthorized),
    ({
        'limits': {
            'perTransaction': '100',
            'weekly': '150'
        }
    }, (400, 'Invalid content', 'error'), True, _rss_failure),
    ({
        'payment_info': {
            'number': '1234',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        }
    }, (400, 'Invalid credit card number', 'error'), True),
    ])
    def test_update_organization(self, data, exp_resp, error, side_effect=None):
        # Create object
        org_entry = views.OrganizationEntry(permitted_methods=('GET', 'PUT'))

        # Include data
        self.request.raw_post_data = json.dumps(data)

        if side_effect:
            side_effect(self)

        # Call the view
        response = org_entry.update(self.request, 'test_org')

        # Check response
        content = json.loads(response.content)
        self.assertEquals(response.status_code, exp_resp[0])
        self.assertEquals(content['message'], exp_resp[1])
        self.assertEquals(content['result'], exp_resp[2])

        # Check values
        if not error:
            if 'notification_url' in data:
                self.assertEquals(data['notification_url'], self.org_object.notification_url)

            if 'tax_address' in data:
                self.assertEquals(data['tax_address'], self.org_object.tax_address)

            if 'payment_info' in data:
                if not data['payment_info']['number'].startswith('x'):
                    self.assertEquals(data['payment_info'], self.org_object.payment_info)
                else:
                    data['payment_info']['number'] = '4567456745674567'

            if 'limits' in data:
                data['limits']['currency'] = 'EUR'
                self.assertEquals(data['limits'], self.org_object.expenditure_limits)
