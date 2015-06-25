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

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from wstore.store_commons.errors import ConflictError
from wstore.admin.repositories.repositories_management import register_repository, unregister_repository, \
    get_repositories, set_default_repository
from wstore.models import Repository
from wstore.admin.repositories import views
from wstore.store_commons.utils.testing import decorator_mock, build_response_mock,\
    decorator_mock_callable, HTTPResponseMock
from wstore.store_commons.utils import http


__test__ = False


class RegisteringRepositoriesTestCase(TestCase):

    tags = ('fiware-ut-10', 'repository')
    fixtures = ['reg_rep.json']

    @parameterized.expand([
        ('basic', {
            'name': 'test_repository',
            'host': 'http://testrepository.com/',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'resourceCollection',
            'api_version': 1,
            'default': False
        }),
        ('basic_2', {
            'name': 'test_repository',
            'host': 'http://testrepository.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'resourceCollection',
            'api_version': 1,
            'default': False
        }),
        ('existing_name', {
            'name': 'test_repository1',
            'host': 'http://testrepository.com/',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'resourceCollection',
            'api_version': 2,
            'default': False
        }, ConflictError, 'The given repository is already registered'),
        ('existing_host', {
            'name': 'test_repository',
            'host': 'http://testrepository1.com/',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'resourceCollection',
            'api_version': 2,
            'default': False
        }, ConflictError, 'The given repository is already registered'),
        ('new_default', {
            'name': 'test_repository',
            'host': 'http://testrepository.com/',
            'resource_collection': 'resourceCollection',
            'offering_collection': 'storeOfferingCollection',
            'api_version': 2,
            'default': True
        }),
    ])
    def test_repository_registering(self, name, data, err_type=None, err_msg=None):

        error = None
        try:
            register_repository(
                data['name'],
                data['host'],
                data['offering_collection'],
                data['resource_collection'],
                data['api_version'],
                default=data['default']
            )
        except Exception as e:
            error = e

        if err_type is None:
            self.assertEquals(error, None)

            if not data['host'].endswith('/'):
                data['host'] += '/'

            rep = Repository.objects.get(name=data['name'], host=data['host'])

            self.assertEqual(data['name'], rep.name)
            self.assertEqual(data['host'], rep.host)
            self.assertEquals(data['default'], rep.is_default)
            self.assertEquals(data['offering_collection'], rep.offering_collection)
            self.assertEquals(data['resource_collection'], rep.resource_collection)
            self.assertEqual(data['api_version'], rep.api_version)

            # Check that the default repository has been to to false
            if data['default']:
                self.assertFalse(Repository.objects.get(pk="61001bba8e05ac2115f11111").is_default)

        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)

    def test_first_repository_registering(self):

        for r in Repository.objects.all():
            r.delete()

        register_repository('test_repository', 'http://testrepository.com', 'testColl', 2, False)
        rep = Repository.objects.get(name='test_repository')
        self.assertTrue(rep.is_default)


class UnregisteringRepositoriesTestCase(TestCase):

    tags = ('fiware-ut-11', 'repository')
    fixtures = ['reg_rep.json']

    def _unregister_repository(self, repository):
        unregister_repository(repository)

        deleted = False
        try:
            Repository.objects.get(name=repository)
        except:
            deleted = True

        return deleted

    def test_basic_unregistering_rep(self):
        deleted = self._unregister_repository('test_repository1')
        self.assertTrue(deleted)

    def test_unregistering_default(self):
        deleted = self._unregister_repository('test_repository2')
        self.assertTrue(deleted)

        # Check that another repository has be set as default
        rep = Repository.objects.get(pk="61001bba8e05ac2115f022f9")
        self.assertTrue(rep.is_default)

    def test_unregister_not_existing_rep(self):

        error = None
        try:
            unregister_repository('test_repository3')
        except Exception as e:
            error = e

        self.assertTrue(isinstance(error, ObjectDoesNotExist))
        self.assertEqual(unicode(error), 'The specified repository does not exist')


class RepositoriesRetrievingTestCase(TestCase):

    tags = ('repository', )
    fixtures = ['reg_rep.json']

    def test_basic_retrieving_repositories(self):

        rep = get_repositories()

        self.assertEqual(rep[0]['name'], 'test_repository1')
        self.assertEqual(rep[0]['host'], 'http://testrepository1.com/')
        self.assertFalse(rep[0]['is_default'])
        self.assertEqual(rep[1]['name'], 'test_repository2')
        self.assertEqual(rep[1]['host'], 'http://testrepository2.com/')
        self.assertTrue(rep[1]['is_default'])


class SetDefaultRepositoryTestCase(TestCase):
    tags = ('repository', )
    fixtures = ['reg_rep.json']

    @parameterized.expand([
        ('basic', "test_repository1"),
        ('not_found', "test_repository3", True)
    ])
    def test_set_default_respository(self, name, repository, error_expected=False):
        error = None
        try:
            set_default_repository(repository)
        except Exception as e:
            error = e

        if not error_expected:
            self.assertEquals(error, None)
            repo1 = Repository.objects.get(name=repository)
            self.assertTrue(repo1.is_default)
            repo2 = Repository.objects.get(name="test_repository2")
            self.assertFalse(repo2.is_default)
        else:
            self.assertTrue(isinstance(error, ObjectDoesNotExist))
            self.assertEquals(unicode(e), 'The specified repository does not exist')


class RepositoryViewTestCase(TestCase):

    tags = ('repository-view', 'repository')

    @classmethod
    def setUpClass(cls):
        # Mock class decorators
        http.authentication_required = decorator_mock
        http.supported_request_mime_types = decorator_mock_callable

        reload(views)
        views.build_response = build_response_mock

        super(RepositoryViewTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Restore mocked decorators
        reload(http)
        reload(views)
        super(RepositoryViewTestCase, cls).tearDownClass()

    def setUp(self):
        # Mock market management methods
        views.register_repository = MagicMock()
        self.request = MagicMock()

    def _forbidden(self):
        self.request.user.is_staff = False

    def _bad_request(self):
        views.register_repository.side_effect = Exception('Bad request')

    def _conflict(self):
        views.register_repository.side_effect = ConflictError('Conflict')

    @parameterized.expand([
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (201, 'Created', 'correct'), False),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
        }, (403, 'You are not authorized to register a repository', 'error'), True, _forbidden),
        ({
            'host': 'http://testrepo.com',
            'store_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Missing required field: name', 'error'), True),
        ({
            'name': 'test_repo',
            'store_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Missing required field: host', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Missing required field: offering_collection', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Missing required field: resource_collection', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
        }, (400, 'Missing required field: api_version', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (500, 'Bad request', 'error'), True, _bad_request),
        ({
            'name': 'test_repo$',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Invalid name format', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'invalid_url',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Invalid URL format', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1as',
        }, (400, 'Invalid api_version format: must be an integer', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '3',
        }, (400, 'Invalid api_version: Only versions 1 and 2 are supported', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOffering Collection',
            'resource_collection': 'storeOfferingCollection',
            'api_version': '1',
        }, (400, 'Invalid offering_collection format: Invalid character found', 'error'), True),
        ({
            'name': 'test_repo',
            'host': 'http://testrepo.com',
            'offering_collection': 'storeOfferingCollection',
            'resource_collection': 'storeOffering Collection',
            'api_version': '1',
        }, (400, 'Invalid resource_collection format: Invalid character found', 'error'), True)
    ])
    def test_repository_api_create(self, data, exp_resp, error, side_effect=None):
        # Create request data
        self.request.raw_post_data = json.dumps(data)

        if side_effect:
            side_effect(self)

        # Create the view
        repo_collection = views.RepositoryCollection(permitted_methods=('POST', 'GET'))

        response = repo_collection.create(self.request)

        # Check response
        content = json.loads(response.content)
        self.assertEquals(response.status_code, exp_resp[0])
        self.assertEquals(content['message'], exp_resp[1])
        self.assertEquals(content['result'], exp_resp[2])

        # Check calls
        if not error:
            views.register_repository.assert_called_with(
                data['name'],
                data['host'],
                data['offering_collection'],
                data['resource_collection'],
                int(data['api_version']),
                False
            )

    @parameterized.expand([
        (False,),
        (True, )
    ])
    def test_repository_api_get(self, error):
        # Mock HttpResponse
        views.HttpResponse = HTTPResponseMock
        # Mock getRepositories
        views.get_repositories = MagicMock()
        data = [{
            'name': 'test_repo',
            'host': 'http://testrepo.com'
        }]
        views.get_repositories.return_value = data

        if error:
            views.get_repositories.side_effect = Exception('Error creating repo')

        repo_collection = views.RepositoryCollection(permitted_methods=('POST', 'GET'))

        response = repo_collection.read(self.request)

        # Check response
        if not error:
            self.assertEquals(json.loads(response.data), data)
            self.assertEquals(response.status, 200)
            self.assertEquals(response.mimetype, 'application/JSON; charset=UTF-8')
        else:
            content = json.loads(response.content)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(content['message'], 'Invalid request')
            self.assertEquals(content['result'], 'error')


class RepositoryEntryTestCase(TestCase):

    tags = ("repository-view", 'repository')

    @classmethod
    def setUpClass(cls):
        # Save modules
        cls._old_resp = views.build_response
        cls._auth_req = http.authentication_required

        # Create mocks
        http.authentication_required = decorator_mock
        reload(views)
        views.build_response = build_response_mock
        super(RepositoryEntryTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        reload(http)
        reload(views)
        super(RepositoryEntryTestCase, cls).tearDownClass()

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_staff = True
        views.unregister_repository = MagicMock()
        views.set_default_repository = MagicMock()
        TestCase.setUp(self)

    def _forbidden(self, method):
        self.request.user.is_staff = False

    def _not_found(self, method):
        method.side_effect = ObjectDoesNotExist('Not found')

    def _call_error(self, method):
        method.side_effect = Exception('Exception')

    def _execute_api_test(self, repo_entry_method, expected_result, called_method):
        response = repo_entry_method(self.request, 'test_repository')

        if expected_result[0] != 403:
            called_method.assert_called_once_with('test_repository')

        content = json.loads(response.content)
        self.assertEquals(response.status_code, expected_result[0])
        self.assertEquals(content['message'], expected_result[1])
        self.assertEquals(content['result'], expected_result[2])

    @parameterized.expand([
        ((204, 'No content', 'correct'),),
        ((403, 'Forbidden', 'error'), _forbidden),
        ((404, 'Not found', 'error'), _not_found),
        ((500, 'Error managing the repository', 'error'), _call_error)
    ])
    def test_repository_api_delete(self, expected_result, side_effect=None):

        if side_effect:
            side_effect(self, views.unregister_repository)

        # Build the view
        repo_entry = views.RepositoryEntry(permitted_methods=('DELETE',))
        self._execute_api_test(repo_entry.delete, expected_result, views.unregister_repository)

    @parameterized.expand([
        ('correct', (200, 'OK', 'correct')),
        ('forbidden', (403, 'Forbidden', 'error'), _forbidden),
        ('not_found', (404, 'Not found', 'error'), _not_found),
        ('exception', (500, 'Error managing the repository', 'error'), _call_error)
    ])
    def test_set_default_repository_api(self, name, expected_result, side_effect=None):
        if side_effect:
            side_effect(self, views.set_default_repository)

        # Build the view
        repo_entry = views.RepositoryDefaultEntry(permitted_methods=('POST',))
        self._execute_api_test(repo_entry.create, expected_result, views.set_default_repository)
