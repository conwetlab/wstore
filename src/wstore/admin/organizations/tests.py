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
from mock import MagicMock
from nose_parameterized import parameterized
from urllib2 import HTTPError

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from wstore.admin.organizations import views
from wstore.store_commons.utils import http
from wstore.models import Organization
from wstore.store_commons.utils.testing import decorator_mock, build_response_mock,\
    decorator_mock_callable, HTTPResponseMock


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
        # Mock class decorators
        http.authentication_required = decorator_mock
        http.supported_request_mime_types = decorator_mock_callable
        cls._old_response = views.HttpResponse

        reload(views)
        views.build_response = build_response_mock
        views.HttpResponse = HTTPResponseMock

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
        views.HttpResponse = cls._old_response
        reload(http)
        reload(views)
        super(OrganizationEntryTestCase, cls).tearDownClass()

    def setUp(self):
        views.RSS = MagicMock()
        self.rss_object = MagicMock()
        views.RSS.objects.all.return_value = [self.rss_object]

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

        views.RSSManagerFactory = MagicMock()
        self._limits_factory = MagicMock()
        views.RSSManagerFactory.return_value = self._limits_factory

        self._exp_mock = MagicMock(name="ExpenditureManager")
        self._limits_factory.get_expenditure_manager.return_value = self._exp_mock

    def _not_found(self):
        views.Organization.objects.get.side_effect = Exception('')

    def _forbidden(self):
        self.org_object.managers = []

    def _unauthorized(self):
        self._exp_mock.set_actor_limit.side_effect = HTTPError('http://rss.test.com', 401, 'Unauthorized', None, None)

    def _rss_failure(self):
        self._exp_mock.set_actor_limit.side_effect = HTTPError('http://rss.test.com', 500, 'Server error', None, None)

    @parameterized.expand([
        ({
            'notification_url': 'http://notificationurl.com',
            'tax_address': {
                'street': 'fake street 123',
                'country': 'Country',
                'city': 'City',
                'province': 'Province',
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
        }, (200, 'OK', 'correct'), False),
        ({}, (200, 'OK', 'correct'), False),
        ({}, (404, 'Organization not found', 'error'), True, _not_found),
        ({}, (403, 'Forbidden', 'error'), True, _forbidden),
        ({
            'notification_url': 'invalidurl'
        }, (400, 'Enter a valid URL', 'error'), True),
        ({
            'limits': {
                'perTransaction': '100',
                'weekly': '150'
            }
        }, (400, 'Invalid JSON content', 'error'), True, _unauthorized),
        ({
            'limits': {
                'perTransaction': '100',
                'weekly': '150'
            }
        }, (400, 'Invalid JSON content', 'error'), True, _rss_failure),
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
                views.RSSManagerFactory.assert_called_once_with(self.rss_object)
                self._limits_factory.get_expenditure_manager.assert_called_once_with(self.rss_object.access_token)
                self._exp_mock.set_actor_limit.assert_called_once_with(data['limits'], self.org_object)

    def _revoke_staff(self):
        self.request.user.is_staff = False

    @parameterized.expand([
    (False, False, ),
    (False, True, _revoke_staff),
    (True, False, _not_found)
    ])
    def test_get_organization(self, error, not_staff, side_effect=None):

        self.request.user.is_staff = True
        # Mock get_organization_info
        data = {
            'name': 'test_org1',
            'notification_url': 'http://notificationurl.com',
            'payment_info': {
                'number': 'xxxxxxxxxxxx1234',
                'type': 'visa',
                'expire_year': '2018',
                'expire_month': '5',
                'cvv2': '111'
            }
        }
        views.get_organization_info = MagicMock()
        views.get_organization_info.return_value = data.copy()

        # Mock organization all method
        org_object = MagicMock()
        views.Organization.objects.get = MagicMock()
        views.Organization.objects.return_value = org_object

        # Create the view
        org_entry = views.OrganizationEntry(permitted_methods=('GET', 'PUT'))

        if side_effect:
            side_effect(self)

        response = org_entry.read(self.request, 'test_org')

        if not error:
            # Check response
            if not_staff:
                del(data['payment_info'])

            self.assertEquals(response.status, 200)
            self.assertEquals(json.loads(response.data), data)
        else:
            body_response = json.loads(response.content)
            self.assertEquals(response.status_code, 404)
            self.assertEquals(body_response['message'], 'Not found')
            self.assertEquals(body_response['result'], 'error')


BASIC_ORGANIZATION = {
    'name': 'test_org1',
    'notification_url': 'http://notificationurl.com'
}


class OrganizationCollectionTestCase(TestCase):

    tags = ('org-admin',)

    @classmethod
    def setUpClass(cls):

        # Mock class decorators
        http.authentication_required = decorator_mock
        http.supported_request_mime_types = decorator_mock_callable
        cls._old_http_response = views.HttpResponse

        reload(views)
        views.build_response = build_response_mock
        views.HttpResponse = HTTPResponseMock
        super(OrganizationCollectionTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Restore mocked decorators
        views.HttpResponse = cls._old_http_response
        reload(http)
        reload(views)
        super(OrganizationCollectionTestCase, cls).tearDownClass()

    def setUp(self):
        # Create organization mock 1
        org_mock_1 = MagicMock()
        org_mock_1.private = False
        org_mock_1.name = 'test_org1'
        org_mock_1.notification_url = 'http://notification.com'
        org_mock_1.tax_address = {
            'street': 'fake street 123',
            'country': 'Country'
        }
        org_mock_1.expenditure_limits = {}
        org_mock_1.payment_info = {
            'number': '1234123412341234',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        }

        # Create organization mock 2
        org_mock_2 = MagicMock()
        org_mock_2.private = False
        org_mock_2.name = 'test_org2'
        org_mock_2.notification_url = 'http://notification2.com'
        org_mock_2.expenditure_limits = {}

        # Create organization mock 3
        org_mock_3 = MagicMock()
        org_mock_3.private = True

        self.organizations = {
            'org1': org_mock_1,
            'org2': org_mock_2,
            'org3': org_mock_3
        }
        # Create request mock
        self.request = MagicMock()
        self.request.user.is_staff = True
        self.request.user.pk = '54321'
        self.request.user.userprofile.organizations = []

        # Create organization object mock
        views.Organization = MagicMock()
        self.created_org = MagicMock()
        self.created_org.managers = []
        self.created_org.pk = "12345"
        views.Organization.objects.get.return_value = self.created_org

    @parameterized.expand([
    ({
        'name': 'test_org1',
        'notification_url': 'http://notification.com',
        'tax_address': {
            'street': 'fake street 123',
            'country': 'Country'
        },
        'payment_info': {
            'number': 'xxxxxxxxxxxx1234',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        },
        'limits': {},
        'is_manager': False
    }, 'org1'),
    ({
        'name': 'test_org2',
        'notification_url': 'http://notification2.com',
        'limits': {},
        'is_manager': False
    }, 'org2'),
    ('Private organization', 'org3', True)
    ])
    def test_get_organization_info(self, exp_data, org_id, exp_error=False):

        # Call the mocked function
        error = False
        msg = None
        try:
            org_info = views.get_organization_info(self.organizations[org_id])
        except Exception as e:
            error = True
            msg = e.message

        if not exp_error:
            # Check organization info
            self.assertFalse(error)
            self.assertEquals(org_info, exp_data)
        else:
            self.assertTrue(error)
            self.assertEquals(msg, exp_data)

    def _not_found(self):
        views.Organization.objects.filter.return_value = []

    def _found(self):
        org = MagicMock()
        views.Organization.objects.filter.return_value = [org]

    def _not_active(self):
        self.request.user.is_active = False

    def _revoke_staff(self):
        self.request.user.is_staff = False

    @parameterized.expand([
    ({
        'name': 'test_org1',
        'notification_url': 'http://notificationurl.com',
        'tax_address': {
            'city': 'city',
            'street': 'fake street 123',
            'country': 'country',
            'province': 'province',
            'postal': '12344'
        },
        'payment_info': {
            'number': '1234123412341234',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        }
    }, (201, 'Created', 'correct'), True, _not_found),
    (BASIC_ORGANIZATION, (201, 'Created', 'correct')),
    ({
      'name': 'test_org1'
      }, (201, 'Created', 'correct')),
    ({
      'name': 'test_org1'
      }, (201, 'Created', 'correct'), True, _revoke_staff, True),
    ({ 
       'notification_url': 'http://notificationurl.com'
    }, (400, 'Invalid JSON content', 'error'), False),
    (BASIC_ORGANIZATION, (400, 'The test_org1 organization is already registered.', 'error'), False, _found),
    ({
       'name': 'test_org1',
       'notification_url': 'http:notificationurl.com'
    }, (400, 'Enter a valid URL', 'error'), False , _not_found),
    (BASIC_ORGANIZATION, (403, 'The user has not been activated', 'error'), False , _not_active),
    ({
      'name': 'test_org1%&',
      'notification_url': 'http://notification.com'
      }, (400, 'Enter a valid name.', 'error'), False),
    ({
      'name': 'test_org1',
      'payment_info': {
            'number': 'invalid',
            'type': 'visa',
            'expire_year': '2018',
            'expire_month': '5',
            'cvv2': '111'
        }
      }, (400, 'Invalid credit card info', 'error'), False),
    ])
    def test_organization_creation(self, data, exp_resp, created=True, side_effect=None, user_included=False):

        # Load request data
        self.request.raw_post_data = json.dumps(data)

        if side_effect:
            side_effect(self)

        # Create the view
        org_collection = views.OrganizationCollection(permitted_methods=('POST', 'GET'))

        # Call the view
        response = org_collection.create(self.request)

        # Check response
        content = json.loads(response.content)
        self.assertEquals(response.status_code, exp_resp[0])
        self.assertEquals(content['message'], exp_resp[1])
        self.assertEquals(content['result'], exp_resp[2])

        # Check calls
        if created:
            tax = {}
            if 'tax_address' in data:
                tax = data['tax_address']

            pay = {}
            if 'payment_info' in data:
                pay = data['payment_info']

            if not 'notification_url' in data:
                data['notification_url'] = ''

            views.Organization.objects.create.assert_called_once_with(
                name=data['name'],
                notification_url=data['notification_url'],
                tax_address=tax,
                payment_info=pay,
                private=False
            )
            # Check if the user has beed included in the organization
            if user_included:
                # Check if the user has beed included in the organization
                self.assertEquals(len(self.request.user.userprofile.organizations), 1)
                self.assertEquals(self.request.user.userprofile.organizations[0], {
                    'organization': self.created_org.pk,
                    'roles': []
                })
                views.Organization.objects.get.assert_called_once_with(name=data['name'])
                self.assertEquals(len(self.created_org.managers), 1)
                self.assertEquals(self.created_org.managers[0], self.request.user.pk)
            else:
                self.assertEquals(len(self.request.user.userprofile.organizations), 0)

    @parameterized.expand([
    (False, ),
    (True, _revoke_staff),
    ])
    def test_organization_retrieving(self, not_staff, side_effect=None):

        # Mock get_organization_info
        data = {
            'name': 'test_org1',
            'notification_url': 'http://notificationurl.com',
            'payment_info': {
                'number': 'xxxxxxxxxxxx1234',
                'type': 'visa',
                'expire_year': '2018',
                'expire_month': '5',
                'cvv2': '111'
            }
        }
        views.get_organization_info = MagicMock()
        views.get_organization_info.return_value = data.copy()

        # Mock organization all method
        views.Organization.objects.all.return_value = [self.organizations['org1'], self.organizations['org2']]

        # Create the view
        org_collection = views.OrganizationCollection(permitted_methods=('POST', 'GET'))

        if side_effect:
            side_effect(self)

        response = org_collection.read(self.request)

        # Check response
        if not_staff:
            del(data['payment_info'])

        self.assertEquals(response.status, 200)
        self.assertEquals(json.loads(response.data), [data, data])
