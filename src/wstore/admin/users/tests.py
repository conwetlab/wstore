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
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.admin.users import views
from wstore.store_commons.utils.testing import decorator_mock, build_response_mock,\
decorator_mock_callable, HTTPResponseMock


class FakeProfile():

    objects = None

    def __init__(self):
        self.objects = self.ObjectsClass()

    class ObjectsClass():

        def get(self, user=None):
            # Build userprofile mocks
            userprofile_1 = MagicMock()
            userprofile_1.complete_name = 'Test user1'
            userprofile_1.current_organization.name = 'test_org1'
            userprofile_1.organizations = [{
                'organization': '1111',
                'roles': ['provider', 'customer']
            }]

            userprofile_1.tax_address = {}
            userprofile_1.payment_info = {
                'number': '1234123412341234',
                'type': 'visa',
                'expire_year': '2018',
                'expire_month': '5',
                'cvv2': '111'
            }
            userprofile_1.get_user_roles = MagicMock()
            userprofile_1.get_user_roles.return_value = ['customer', 'provider']

            userprofile_2 = MagicMock()
            userprofile_2.complete_name = 'Test user2'
            userprofile_2.current_organization.name = 'test_org2'
            userprofile_2.actor_id = 1
            userprofile_2.tax_address = {}
            userprofile_2.payment_info = {}
            userprofile_2.organizations = [{
                'organization': '2222',
                'roles': ['customer']
            }]

            userprofile_2.get_user_roles = MagicMock()
            userprofile_2.get_user_roles.return_value = ['customer']

            profiles = {
                'user1': userprofile_1,
                'user2': userprofile_2,
            }
            return profiles[user.username]


class FakeOrganization():

    objects = None

    def __init__(self):
        self.objects = self.ObjectsClass()

    class ObjectsClass():

        def get(self, pk=None, name=None, actor_id=None):
            org = None
            org_object_private_1 = MagicMock()
            org_object_private_1.name = 'user1'
            org_object_private_1.notification_url = 'http://examplenot1.com'

            org_object_private_2 = MagicMock()
            org_object_private_2.name = 'user2'
            org_object_private_2.notification_url = 'http://examplenot4.com'

            org_object_1 = MagicMock()
            org_object_1.name = 'test_org1'
            org_object_1.notification_url = 'http://examplenot2.com'
            org_object_1.managers = ['1122']

            org_object_2 = MagicMock()
            org_object_2.name = 'test_org2'
            org_object_2.notification_url = 'http://examplenot3.com'
            org_object_2.managers = ['3333']

            if name:
                if name == 'user1':
                    org = org_object_private_1
                elif name == 'user2':
                    org = org_object_private_2
            elif pk:
                if pk == '1111':
                    org = org_object_1
                elif pk == '2222':
                    org = org_object_2
            elif actor_id and actor_id == 1:
                org = org_object_private_2

            return org


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

    def test_user_creation(self):
        pass


class UserEntryTestCase(TestCase):

    def test_user_retrieving(self):
        pass

    def test_user_update(self):
        pass
