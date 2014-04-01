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

import types
import json
from mock import MagicMock
from urllib2 import HTTPError
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.admin.users import views
from wstore.store_commons.utils.testing import decorator_mock, build_response_mock,\
decorator_mock_callable, HTTPResponseMock
from wstore.admin.rss.tests import ExpenditureMock


class FakeProfile():

    objects = None

    def __init__(self):
        self.objects = self.ObjectsClass()

    class ObjectsClass():

        def __init__(self):
            # Build userprofile mocks
            self.userprofile_1 = MagicMock()
            self.userprofile_1.complete_name = 'Test user1'
            self.userprofile_1.current_organization.name = 'test_org1'
            self.userprofile_1.organizations = [{
                'organization': '1111',
                'roles': ['provider', 'customer']
            }]

            self.userprofile_1.tax_address = {}
            self.userprofile_1.payment_info = {
                'number': '1234123412341234',
                'type': 'visa',
                'expire_year': '2018',
                'expire_month': '5',
                'cvv2': '111'
            }
            self.userprofile_1.get_user_roles = MagicMock()
            self.userprofile_1.get_user_roles.return_value = ['customer', 'provider']

            self.userprofile_2 = MagicMock()
            self.userprofile_2.complete_name = 'Test user2'
            self.userprofile_2.current_organization.name = 'test_org2'
            self.userprofile_2.actor_id = 1
            self.userprofile_2.tax_address = {}
            self.userprofile_2.payment_info = {}
            self.userprofile_2.organizations = [{
                'organization': '2222',
                'roles': ['customer']
            }]

            self.userprofile_2.get_user_roles = MagicMock()
            self.userprofile_2.get_user_roles.return_value = ['customer']

            self.userprofile_3 = MagicMock()
            self.userprofile_3.complete_name = 'Test user3 initial'
            self.userprofile_3.current_organization.name = 'test_org3'
            self.userprofile_3.organizations = [{
                'organization': '3333',
                'roles': ['customer']
            }, {
                'organization': '4444',
                'roles': ['customer']
            }]
            self.userprofile_3.payment_info = {
                'number': '4567456745674567'
            }
            self.userprofile_3.get_user_roles = MagicMock()
            self.userprofile_3.get_user_roles.return_value = ['customer', 'provider']

        def get(self, user=None):

            profiles = {
                'user1': self.userprofile_1,
                'user2': self.userprofile_2,
                'user3': self.userprofile_3
            }
            return profiles[user.username]


class FakeOrganization():

    objects = None

    def __init__(self):
        self.objects = self.ObjectsClass()

    class ObjectsClass():

        def __init__(self):
            self.org_object_private_1 = MagicMock()
            self.org_object_private_1.name = 'user1'
            self.org_object_private_1.notification_url = 'http://examplenot1.com'

            self.org_object_private_2 = MagicMock()
            self.org_object_private_2.name = 'user2'
            self.org_object_private_2.notification_url = 'http://examplenot4.com'

            self.org_object_private_3 = MagicMock()
            self.org_object_private_3.name = 'user3'
            self.org_object_private_3.notification_url = 'http://examplenot5.com'

            self.org_object_1 = MagicMock()
            self.org_object_1.name = 'test_org1'
            self.org_object_1.notification_url = 'http://examplenot2.com'
            self.org_object_1.managers = ['1122']

            self.org_object_2 = MagicMock()
            self.org_object_2.name = 'test_org2'
            self.org_object_2.notification_url = 'http://examplenot3.com'
            self.org_object_2.managers = ['3333']

            self.org_object_3 = MagicMock()
            self.org_object_3.name = 'test_org3'
            self.org_object_3.notification_url = 'http://examplenot6.com'
            self.org_object_3.managers = ['3333']

        def get(self, pk=None, name=None, actor_id=None):

            orgs = {
                'user1': self.org_object_private_1,
                'user2': self.org_object_private_2,
                '1111': self.org_object_1,
                '2222': self.org_object_2,
                '3333': self.org_object_3,
                '4444': self.org_object_private_3,
                1: self.org_object_private_2,
                'user3': self.org_object_private_3,
                2: self.org_object_private_3
            }

            key = None
            if pk:
                key = pk
            elif name:
                key = name
            elif actor_id:
                key = actor_id

            return orgs[key]


class UserCollectionTestCase(TestCase):

    tags = ('user-admin',)

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
        cls.views = views
        cls.views.build_response = build_response_mock
        # Mock Userprofile
        views.UserProfile = FakeProfile()
        views.Organization = FakeOrganization()
        super(UserCollectionTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Restore mocked decorators
        from wstore.store_commons.utils import http
        http.authentication_required = cls._old_auth
        http.supported_request_mime_types = cls._old_supp
        super(UserCollectionTestCase, cls).tearDownClass()

    def setUp(self):
        # Create request mock
        self.request = MagicMock()
        self.request.user = MagicMock()
        self.request.user.is_staff = True

        # Create user mocks
        user_mock1 = MagicMock()
        user_mock1.username = 'user1'
        user_mock1.first_name = 'Test'
        user_mock1.last_name = 'user1'
        user_mock1.pk = '1122'
        user_mock1.is_staff = True

        user_mock2 = MagicMock()
        user_mock2.username = 'user2'
        user_mock2.first_name = 'Test'
        user_mock2.last_name = 'user2'
        user_mock2.is_staff = False
        self.user_mocks = {
            'user1': user_mock1,
            'user2': user_mock2,
        }

    @parameterized.expand([
    (['user1', 'user2'], False, [{
        'username': 'user1',
        'complete_name': 'Test user1',
        'first_name': 'Test',
        'last_name': 'user1',
        'current_organization': 'test_org1',
        'organizations': [{
            'name': 'test_org1',
            'roles': ['provider', 'customer', 'manager'],
            'notification_url': 'http://examplenot2.com',
        }],
        'notification_url': 'http://examplenot1.com',
        'tax_address': {},
        'roles': ['customer', 'provider', 'admin'],
        'payment_info': {
                'number': 'xxxxxxxxxxxx1234',
                'type': 'visa',
                'expire_year': '2018',
                'expire_month': '5',
                'cvv2': '111'
        }
    }, {
       'username': 'user2',
       'complete_name': 'Test user2',
       'first_name': 'Test',
       'last_name': 'user2',
       'current_organization': 'test_org2',
       'organizations': [{
            'name': 'test_org2',
            'roles': ['customer']
        }],
       'notification_url': 'http://examplenot4.com',
       'tax_address': {},
       'roles':['customer'],
       'payment_info': {}
    }], 200, False),
    (['user2'], False, [{
       'username': 'user2',
       'complete_name': 'Test user2',
       'current_organization': 'test_org2',
       'organizations': [{
            'name': 'test_org2',
            'roles': ['customer']
        }],
       'notification_url': 'http://examplenot4.com',
       'tax_address': {},
       'roles':['customer'],
       'payment_info': {}
    }], 200, True),
    (['user1'], True, ('error', 'Forbidden'), 403, False)
    ])
    def test_user_retrieving(self, users, error, expected_response, code, ext_auth):
        # Mock User all method
        views.User = MagicMock()
        views.User.objects.all = MagicMock()
        views.User.objects.all.return_value = [self.user_mocks[u] for u in users]

        # Mock settings
        views.settings.OILAUTH = ext_auth

        # Mock HTTPResponse
        views.HttpResponse = HTTPResponseMock

        collection = views.UserProfileCollection(permitted_methods=('GET', 'POST'))

        if error:
            self.request.user.is_staff = False

        response = collection.read(self.request)

        # Check response
        if not error:
            data = json.loads(response.data)
            self.assertEquals(len(data), len(expected_response))

            matches = 0
            for elem in data:
                for exp_elem in expected_response:
                    if elem['username'] == exp_elem['username']:
                        self.assertEquals(elem, exp_elem)
                        matches += 1

            self.assertEquals(matches, len(expected_response))

            self.assertEquals(code, response.status)
            self.assertEquals('application/json', response.mimetype)
        else:
            data = json.loads(response.content)
            self.assertEquals(response.status_code, code)
            self.assertEquals(data['result'], expected_response[0])
            self.assertEquals(data['message'], expected_response[1])


class UserEntryTestCase(TestCase):

    tags = ('user-admin',)

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
        cls.views = views
        cls.views.build_response = build_response_mock
        cls.views._check_limits = MagicMock()
        cls.views._check_limits.return_value = {
            'currency': 'EUR',
            'perTransaction': 100.0,
            'weekly': 150.0
        }
        cls.views.RSS = MagicMock()
        rss_object = MagicMock()
        cls.views.RSS.objects.all.return_value = [rss_object]
        super(UserEntryTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Restore mocked decorators
        from wstore.store_commons.utils import http
        http.authentication_required = cls._old_auth
        http.supported_request_mime_types = cls._old_supp
        super(UserEntryTestCase, cls).tearDownClass()

    def setUp(self):
        # Create mock request
        user_object = MagicMock()
        user_object.is_staff = True
        user_object.userprofile.actor_id = 2

        self.request = MagicMock()
        self.request.user = user_object

        # Mock user
        views.User = MagicMock()
        views.User.objects.get = MagicMock()
        views.User.objects.get.return_value = user_object

        # Mock Userprofile
        views.UserProfile = FakeProfile()
        views.Organization = FakeOrganization()

    def test_user_retrieving(self):
        pass

    def _provider_org(self):
        up = views.UserProfile.objects.get(user=self.request.user)
        up.organizations = [{
            'organization': '3333',
            'roles': ['customer']
        }, {
            'organization': '4444',
            'roles': ['customer', 'provider']
        }]

    def _not_provider(self):
        up = views.UserProfile.objects.get(user=self.request.user)
        up.get_user_roles.return_value = ['customer']

    def _mock_expenditure(self):
        views.ExpenditureManager = MagicMock()

    def _mock_expenditure_401(self):
        exp_mock = ExpenditureMock()
        views.ExpenditureManager = exp_mock.ExpenditureManager

    def _revoke_staff(self):
        self.request.user.is_staff = False
        self.request.user.username = 'user3'

    def _unauthorized(self):
        exp_object = MagicMock()
        exp_object.set_actor_limit.side_effect = HTTPError('http://rss.test.com', 401, 'Unauthorized', None, None)
        views.ExpenditureManager = MagicMock()
        views.ExpenditureManager.return_value = exp_object

    @parameterized.expand([
    ({
        'roles': ['admin', 'provider'],
        'notification_url': 'http://newnotification.com',
        'password': '12345',
        'first_name': 'Test',
        'last_name': 'user3',
        'tax_address': {
            'street': 'fake street 123',
            'postal': '123451',
            'city': 'City',
            'country': 'Country'
        },
        'payment_info': {
            'number': '1234123412341234',
            'type': 'Visa',
            'expire_month': '5',
            'expire_year': '2018',
            'cvv2': '121'
        }
    }, 'user3', False, (200, 'OK', 'correct'), False),
    ({
        'roles': [],
        'complete_name': 'Test user3-2',
    }, 'user3', False, (200, 'OK', 'correct'), False, _provider_org),
    ({
        'roles': [],
        'payment_info': {
            'number': 'xxxxxxxxxxxx4567',
            'type': 'Visa',
            'expire_month': '5',
            'expire_year': '2018',
            'cvv2': '121'
        }
    }, 'user3', False, (200, 'OK', 'correct'), False, _not_provider),
    ({
        'tax_address': {
            'street': 'fake street 123',
            'postal': '123451',
            'city': 'City',
            'country': 'Country'
        }
    }, 'user3', False, (200, 'OK', 'correct'), False),
    ({
        'notification_url': 'http://newnotificationurl.com',
        'limits': {
            'perTransaction': '100',
            'weekly': '150',
        }
    }, 'user3', True, (200, 'OK', 'correct'), False, _mock_expenditure),
    ({
        'notification_url': 'http://newnotificationurl.com',
        'limits': {
            'perTransaction': '100',
            'weekly': '150',
        }
    }, 'user3', True, (200, 'OK', 'correct'), False, _mock_expenditure_401),
    ({
        'notification_url': 'http://newnotificationurl.com',
        'limits': {
            'perTransaction': '100',
            'weekly': '150',
        }
    }, 'user4', True, (403, 'Forbidden', 'error'), True, _revoke_staff),
    ({
        'notification_url': 'http://newnotificationurl.com',
        'limits': {
            'perTransaction': '100',
            'weekly': '150',
        }
    }, 'user3', True, (400, 'Invalid content', 'error'), True, _unauthorized),
    ({
        'roles': [],
        'payment_info': {
            'number': 'xxxxxxxxxxxx3333',
            'type': 'Visa',
            'expire_month': '5',
            'expire_year': '2018',
            'cvv2': '121'
        }
    }, 'user3', True, (400, 'Invalid content', 'error'), True)
    ])
    def test_user_update(self, data, username, idm_auth, exp_resp, error, side_effect=None):
        """
        Test user update
        """
        self.request.user.username = username
        views.settings.OILAUTH = idm_auth

        # Include data request
        self.request.raw_post_data = json.dumps(data)

        # Create view class
        user_entry = views.UserProfileEntry(permitted_methods=('GET', 'PUT'))

        # Create side effect if needed
        if side_effect:
            side_effect(self)

        # Call the view
        response = user_entry.update(self.request, username)

        # Check response
        content = json.loads(response.content)
        self.assertEquals(response.status_code, exp_resp[0])
        self.assertEquals(content['message'], exp_resp[1])
        self.assertEquals(content['result'], exp_resp[2])

        # Check calls and updates
        if not error:
            # Get the mocked profile
            userprofile = views.UserProfile.objects.get(user=self.request.user)
            if 'tax_address' in data:
                self.assertEquals(data['tax_address'], userprofile.tax_address)

            if 'payment_info' in data and not data['payment_info']['number'].startswith('x'):
                self.assertEquals(data['payment_info'], userprofile.payment_info)

            if 'first_name' in data:
                self.assertEquals(data['first_name'], self.request.user.first_name)
                self.assertEquals(data['last_name'], self.request.user.last_name)
                self.assertEquals(data['first_name'] + ' ' + data['last_name'], userprofile.complete_name)
            elif 'complete_name' in data:
                self.assertEquals(data['complete_name'], userprofile.complete_name)

            if 'notification_url' in data:
                # Get org
                org = views.Organization.objects.get(name=username)
                self.assertEquals(data['notification_url'], org.notification_url)

            # Check roles
            if 'roles' in data:
                for o in userprofile.organizations:
                    if views.Organization.objects.get(pk=o['organization']).name == username:
                        for role in data['roles']:
                            if role != 'admin':
                                self.assertTrue(role in o['roles'])
                            else:
                                self.assertTrue(self.request.user.is_staff)
