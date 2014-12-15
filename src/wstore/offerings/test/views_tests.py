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

from mock import MagicMock
from urllib2 import HTTPError
from StringIO import StringIO
from nose_parameterized import parameterized

from django.test import TestCase
from django.test.client import RequestFactory, MULTIPART_CONTENT
from django.contrib.auth.models import User

from wstore.offerings import views
from wstore.models import Offering, Organization, Context
from django.contrib.sites.models import Site
from social_auth.db.django_models import UserSocialAuth


class OfferingCollectionTestCase(TestCase):

    tags = ('offering-api',)

    @classmethod
    def setUpClass(cls):
        super(OfferingCollectionTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        from wstore.offerings import offerings_management
        reload(offerings_management)
        reload(views)
        super(OfferingCollectionTestCase, cls).tearDownClass()

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(
            username='test_user',
            email='',
            password='passwd'
        )

    def test_get_offering_request(self):

        return_value = [{
            'name': 'test_offering1',
            'owner_organization': 'test_organization1',
            'owner_admin_user_id': 'test_user',
            'version': '1.0',
            'state': 'published',
            'description_url': 'http://repository.com/collection/usdl',
            'rating': 0,
            'comments': [],
            'tags': [],
            'image_url': 'media/image.png',
            'related_images': [],
            'creation_date': '2013-05-01 10:00:00',
            'publication_date': '2013-06-03 10:00:00',
            'resources': []
        }]

        # Mock get offerings method
        offering_collection = views.OfferingCollection(permitted_methods=('GET', 'POST'))
        views.get_offerings = MagicMock(name='get_offering')

        # Not counting offerings
        #------------------------------------
        # Published
        #------------------------------------
        views.get_offerings.return_value = return_value
        request = self.factory.get('/api/offering/offerings')
        request.user = self.user

        # Call the view
        response = offering_collection.read(request)

        # Check correct call
        views.get_offerings.assert_called_once_with(self.user, u'published', None, sort=None, pagination=None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/JSON; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), list)
        self.assertEqual(len(body_response), 1)
        value = body_response[0]
        self.assertEqual(value['name'], 'test_offering1')
        self.assertEqual(value['owner_organization'], 'test_organization1')
        self.assertEqual(value['owner_admin_user_id'], 'test_user')

        #------------------------------------
        # Provided
        #------------------------------------

        views.get_offerings.reset_mock()
        request = self.factory.get('/api/offering/offerings?filter=provided')
        request.user = self.user

        # Call the view
        response = offering_collection.read(request)

        # Check correct call
        views.get_offerings.assert_called_once_with(self.user, 'provided', None, sort=None, pagination=None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/JSON; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), list)
        self.assertEqual(len(body_response), 1)
        value = body_response[0]
        self.assertEqual(value['name'], 'test_offering1')
        self.assertEqual(value['owner_organization'], 'test_organization1')
        self.assertEqual(value['owner_admin_user_id'], 'test_user')

        #--------------------------------------
        # Purchased
        #--------------------------------------
        views.get_offerings.reset_mock()
        request = self.factory.get('/api/offering/offerings?filter=purchased')
        request.user = self.user

        # Call the view
        response = offering_collection.read(request)

        # Check correct call
        views.get_offerings.assert_called_once_with(self.user, 'purchased', None, sort=None, pagination=None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/JSON; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), list)
        self.assertEqual(len(body_response), 1)
        value = body_response[0]
        self.assertEqual(value['name'], 'test_offering1')
        self.assertEqual(value['owner_organization'], 'test_organization1')
        self.assertEqual(value['owner_admin_user_id'], 'test_user')

        # Counting offerings
        views.count_offerings = MagicMock(name='count_offerings')
        views.count_offerings.return_value = {
            'number': 3
        }

        #----------------------------------------
        # Published
        #----------------------------------------
        request = self.factory.get('/api/offering/offerings?action=count')
        request.user = self.user

        # Call the view
        response = offering_collection.read(request)

        # Check correct call
        views.count_offerings.assert_called_once_with(self.user, 'published', None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/JSON; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['number'], 3)

        #----------------------------------------
        # Provided
        #----------------------------------------
        views.count_offerings.reset_mock()
        request = self.factory.get('/api/offering/offerings?action=count&filter=provided')
        request.user = self.user

        # Call the view
        response = offering_collection.read(request)

        # Check correct call
        views.count_offerings.assert_called_once_with(self.user, 'provided', None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/JSON; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['number'], 3)
        #----------------------------------------
        # Purchased
        #----------------------------------------
        views.count_offerings.reset_mock()
        request = self.factory.get('/api/offering/offerings?action=count&filter=purchased')
        request.user = self.user

        # Call the view
        response = offering_collection.read(request)

        # Check correct call
        views.count_offerings.assert_called_once_with(self.user, 'purchased', None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/JSON; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['number'], 3)

    def test_create_offering_correct_request(self):

        data = {
            'name': 'test_offering',
            'version': 1.0,
            'description': 'test offering'
        }
        views.create_offering = MagicMock(name='create_offering')
        offering_collection = views.OfferingCollection(permitted_methods=('GET', 'POST'))

        request = self.factory.post(
            '/api/offering/offerings',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['provider', 'customer']
        self.user.userprofile.save()
        request.user = self.user

        # Call the view
        response = offering_collection.create(request)

        # Check correct call
        views.create_offering.assert_called_once_with(self.user, data)

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content)
        self.assertEqual(content['message'], 'Created')
        self.assertEqual(content['result'], 'correct')

    def test_create_offering_no_provider(self):
        data = {
            'name': 'test_offering',
            'version': 1.0,
            'description': 'test offering'
        }
        views.create_offering = MagicMock(name='create_offering')
        offering_collection = views.OfferingCollection(permitted_methods=('GET', 'POST'))

        request = self.factory.post(
            '/api/offering/offerings',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['customer']
        self.user.userprofile.save()
        request.user = self.user

        # Call the view
        response = offering_collection.create(request)

        # Check correct call
        self.assertFalse(views.create_offering.called)

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content)
        self.assertEqual(content['message'], 'Forbidden')
        self.assertEqual(content['result'], 'error')

    def test_create_offering_bad_gateway(self):

        data = {
            'name': 'test_offering',
            'version': 1.0,
            'description': 'test offering'
        }
        views.create_offering = MagicMock(name='create_offering')
        views.create_offering.side_effect = HTTPError('', 500, '', None, None)

        offering_collection = views.OfferingCollection(permitted_methods=('GET', 'POST'))

        request = self.factory.post(
            '/api/offering/offerings',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['provider', 'customer']
        self.user.userprofile.save()
        request.user = self.user

        # Call the view
        response = offering_collection.create(request)

        # Check correct call
        views.create_offering.assert_called_once_with(self.user, data)

        self.assertEqual(response.status_code, 502)
        content = json.loads(response.content)
        self.assertEqual(content['message'], 'Bad Gateway')
        self.assertEqual(content['result'], 'error')

    def test_create_offering_Exception(self):

        data = {
            'name': 'test_offering',
            'version': 1.0,
            'description': 'test offering'
        }
        views.create_offering = MagicMock(name='create_offering')
        views.create_offering.side_effect = Exception('Error in creation')

        offering_collection = views.OfferingCollection(permitted_methods=('GET', 'POST'))

        request = self.factory.post(
            '/api/offering/offerings',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['provider', 'customer']
        self.user.userprofile.save()
        request.user = self.user

        # Call the view
        response = offering_collection.create(request)

        # Check correct call
        views.create_offering.assert_called_once_with(self.user, data)

        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertEqual(content['message'], 'Error in creation')
        self.assertEqual(content['result'], 'error')


class OfferingEntryTestCase(TestCase):

    tags = ('offering-api',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')

    @classmethod
    def tearDownClass(cls):
        from wstore.offerings import offerings_management
        reload(offerings_management)
        reload(views)
        super(OfferingEntryTestCase, cls).tearDownClass()

    def test_get_offering(self):

        return_value = {
            'name': 'test_offering',
            'owner_organization': 'test_user',
            'owner_admin_user_id': 'test_user',
            'version': '1.0',
            'state': 'published',
            'description_url': 'http://repository.com/collection/usdl',
            'rating': 0,
            'comments': [],
            'tags': [],
            'image_url': 'media/image.png',
            'related_images': [],
            'creation_date': '2013-05-01 10:00:00',
            'publication_date': '2013-06-03 10:00:00',
            'resources': []
        }

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.get_offering_info = MagicMock(name='get_offering_info')
        views.get_offering_info.return_value = return_value

        request = self.factory.get('/api/offering/offerings/test_user/test_offering/1.0')
        request.user = self.user

        # Call the view
        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=Organization.objects.get(name='test_user'),
            owner_admin_user=self.user,
            version='1.0',
            state='published',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )

        response = offering_entry.read(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        views.get_offering_info.assert_called_once_with(offering, self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['name'], 'test_offering')
        self.assertEqual(body_response['owner_organization'], 'test_user')
        self.assertEqual(body_response['owner_admin_user_id'], 'test_user')

    def test_get_offering_not_found(self):

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.get_offering_info = MagicMock(name='get_offering_info')

        request = self.factory.get('/api/offering/offerings/test_user/test_offering/1.0', HTTP_ACCEPT='application/json')
        request.user = self.user

        response = offering_entry.read(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        self.assertFalse(views.get_offering_info.called)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Offering not found')
        self.assertEqual(body_response['result'], 'error')

    def test_get_offering_exception(self):

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.get_offering_info = MagicMock(name='get_offering_info')
        views.get_offering_info.side_effect = Exception('Error getting offering')

        request = self.factory.get('/api/offering/offerings/test_user/test_offering/1.0', HTTP_ACCEPT='application/json')
        request.user = self.user

        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=Organization.objects.get(name='test_user'),
            owner_admin_user=self.user,
            version='1.0',
            state='published',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )

        response = offering_entry.read(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        views.get_offering_info.assert_called_once_with(offering, self.user)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Error getting offering')
        self.assertEqual(body_response['result'], 'error')

    def test_offering_update(self):

        data = {
            'name': 'test_offering',
            'version': '1.0',
            'description': 'test offering'
        }

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.update_offering = MagicMock(name='update_offering')

        request = self.factory.put(
            '/api/offering/offerings/test_user/test_offering/1.0',
            json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )

        request.user = self.user

        # Call the view
        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=Organization.objects.get(name='test_user'),
            owner_admin_user=self.user,
            version='1.0',
            state='published',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )
        #views.Offering.is_owner = MagicMock(name='is_owner')
        #views.Offering.is_owner.return_value = True

        response = offering_entry.update(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        views.update_offering.assert_called_once_with(offering, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'OK')
        self.assertEqual(body_response['result'], 'correct')

    def test_offering_update_not_found(self):

        data = {
            'name': 'test_offering',
            'version': '1.0',
            'description': 'test offering'
        }

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.update_offering = MagicMock(name='update_offering')

        request = self.factory.put(
            '/api/offering/offerings/test_user/test_offering/1.0',
            json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )

        request.user = self.user

        response = offering_entry.update(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        self.assertFalse(views.update_offering.called)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Offering not found')
        self.assertEqual(body_response['result'], 'error')

    def test_offering_update_not_provider(self):

        data = {
            'name': 'test_offering',
            'version': '1.0',
            'description': 'test offering'
        }

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.update_offering = MagicMock(name='update_offering')

        request = self.factory.put(
            '/api/offering/offerings/test_user/test_offering/1.0',
            json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )

        request.user = self.user
        org = Organization.objects.get(name='test_user')

        # Call the view
        Offering.objects.create(
            name='test_offering',
            owner_organization=org,
            owner_admin_user=self.user,
            version='1.0',
            state='published',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )
        # Mock offering functions to obtain that the user is not owner
        views.Offering.is_owner = MagicMock(name='is_owner')
        views.Offering.is_owner.return_value = False
        org.managers = []
        org.save()

        response = offering_entry.update(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        self.assertFalse(views.update_offering.called)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'You are not allowed to edit the current offering')
        self.assertEqual(body_response['result'], 'error')

    def test_offering_update_exception(self):

        data = {
            'name': 'test_offering',
            'version': '1.0',
            'description': 'test offering'
        }

        # Mock get offerings method
        offering_entry = views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))
        views.update_offering = MagicMock(name='update_offering')
        views.update_offering.side_effect = Exception('Update error')

        request = self.factory.put(
            '/api/offering/offerings/test_user/test_offering/1.0',
            json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )

        request.user = self.user
        org = Organization.objects.get(name='test_user')

        # Call the view
        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=org,
            owner_admin_user=self.user,
            version='1.0',
            state='published',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )

        response = offering_entry.update(request, 'test_user', 'test_offering', '1.0')

        # Check correct call
        views.update_offering.assert_called_once_with(offering, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Update error')
        self.assertEqual(body_response['result'], 'error')


RESOURCE_DATA = {
    'name': 'test_resource',
    'version': '1.0',
    'description': 'test resource'
}


class ResourceCollectionTestCase(TestCase):

    tags = ('offering-api',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['provider', 'customer']
        self.user.userprofile.save()

    @classmethod
    def tearDownClass(cls):
        from wstore.offerings import offerings_management
        reload(offerings_management)
        reload(views)
        super(ResourceCollectionTestCase, cls).tearDownClass()

    def _no_provider(self):
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['customer']
        self.user.userprofile.save()

    def _call_exception(self):
        views.get_provider_resources.side_effect = Exception('Getting resources error')

    def _creation_exception(self):
        views.register_resource.side_effect = Exception('Resource creation exception')

    @parameterized.expand([
        ([{
            'name': 'test_resource',
            'provider': 'test_user',
            'version': '1.0'
        }],),
        ([], _no_provider, 403, 'Forbidden'),
        ([], _call_exception, 400, 'Getting resources error')
    ])
    def test_get_resources(self, return_value, side_effect=None, code=200, error_msg=None, pagination=None):

        # Mock get offerings method
        resource_collection = views.ResourceCollection(permitted_methods=('GET', 'POST'))
        views.get_provider_resources = MagicMock(name='get_provider_resources')

        views.get_provider_resources.return_value = return_value
        request = self.factory.get('/api/offering/resources', HTTP_ACCEPT='application/json')

        request.user = self.user

        # Create the side effect if needed
        if side_effect:
            side_effect(self)

        # Call the view
        response = resource_collection.read(request)

        self.assertEquals(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        if not error_msg:
            # Check correct call
            views.get_provider_resources.assert_called_once_with(self.user, pagination=None, filter_=None)
            self.assertEquals(type(body_response), list)
            self.assertEquals(body_response, return_value)
        else:
            self.assertEqual(type(body_response), dict)
            self.assertEqual(body_response['message'], error_msg)
            self.assertEqual(body_response['result'], 'error')

    @parameterized.expand([
        (RESOURCE_DATA,),
        (RESOURCE_DATA, True),
        (RESOURCE_DATA, False, _no_provider, True, 403, "You don't have the provider role"),
        (RESOURCE_DATA, False, _creation_exception, True, 400, 'Resource creation exception'),
        (RESOURCE_DATA, True, _creation_exception, True, 400, 'Resource creation exception')
    ])
    def test_create_resource(self, data, file_=False, side_effect=None, error=False, code=201, msg='Created'):

        # Mock get offerings method
        resource_collection = views.ResourceCollection(permitted_methods=('GET', 'POST'))
        views.register_resource = MagicMock(name='get_provider_resources')

        content = json.dumps(data)
        content_type = 'application/json'

        if file_:
            f = StringIO()
            f.name = 'test_file.txt'
            f.write('test file')
            content = {
                'json': json.dumps(data),
                'file': f
            }
            content_type = MULTIPART_CONTENT

        # Build the request
        request = self.factory.post(
            '/api/offering/resources',
            content,
            content_type=content_type,
            HTTP_ACCEPT='application/json'
        )

        request.user = self.user

        # Create the side effect if needed
        if side_effect:
            side_effect(self)

        # Call the view
        response = resource_collection.create(request)

        self.assertEqual(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], msg)

        if not error:
            # Check correct call
            if not file_:
                views.register_resource.assert_called_once_with(self.user, data)
            else:
                expected_file = request.FILES['file']  # The type change when loaded
                views.register_resource.assert_called_once_with(self.user, data, file_=expected_file)

            self.assertEqual(body_response['result'], 'correct')
        else:
            self.assertEqual(body_response['result'], 'error')


class ResourceEntryTestCase(TestCase):

    tags = ('offering-api',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()

        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['provider', 'customer']
        self.user.userprofile.save()

        # Create resource model mock
        self.resource = MagicMock()
        self.resource.provider = self.user.userprofile.current_organization
        views.OfferingResource = MagicMock()
        views.OfferingResource.objects.get.return_value = self.resource

    @classmethod
    def tearDownClass(cls):
        from wstore.offerings import offerings_management
        reload(offerings_management)
        reload(views)
        super(ResourceEntryTestCase, cls).tearDownClass()

    def tearDown(self):
        views.json = json

    def _not_found(self):
        views.OfferingResource.objects.get.side_effect = Exception('Not found')

    def _no_provider(self):
        self.user.userprofile.get_current_roles.return_value = ['customer']

    def _exception_update(self):
        views.update_resource.side_effect = Exception('Exception in call')

    def _exception_upgrade(self):
        views.upgrade_resource.side_effect = Exception('Exception in call')

    def _exception_delete(self):
        views.delete_resource.side_effect = Exception('Exception in call')

    def _invalid_json(self):
        views.json = MagicMock()
        views.json.loads.side_effect = Exception('Invalid content')

    @parameterized.expand([
        (RESOURCE_DATA, 200, 'OK'),
        (RESOURCE_DATA, 400, 'Invalid content', _invalid_json, 'error'),
        (RESOURCE_DATA, 403, 'Forbidden', _no_provider, 'error'),
        (RESOURCE_DATA, 400, 'Exception in call', _exception_update, 'error')
    ])
    def test_resouorce_update_api(self, data, code, msg, side_effect=None, status='correct'):
        views.update_resource = MagicMock(name='update_resource')

        if side_effect:
            side_effect(self)

        request = self.factory.put(
            '/api/offering/resources/test_user/test_resource/1.0',
            json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        request.user = self.user

        res_entry = views.ResourceEntry(permitted_methods=('PUT', 'POST', 'DELETE'))
        response = res_entry.update(request, 'test_user', 'test_resource', '1.0')

        self.assertEqual(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEquals(type(body_response), dict)
        self.assertEquals(body_response['message'], msg)
        self.assertEquals(body_response['result'], status)

        # Check call to update method if needed
        if status != 'error':
            views.update_resource.assert_called_once_with(self.resource, data)

    @parameterized.expand([
        (RESOURCE_DATA, 200, 'OK'),
        (RESOURCE_DATA, 200, 'OK', True),
        (RESOURCE_DATA, 400, 'Invalid content', False, _invalid_json, True),
        (RESOURCE_DATA, 400, 'Invalid content', True, _invalid_json, True),
        (RESOURCE_DATA, 404, 'Resource not found', False, _not_found, True),
        (RESOURCE_DATA, 403, 'Forbidden', False, _no_provider, True),
        (RESOURCE_DATA, 400, 'Exception in call', False, _exception_upgrade, True)
    ])
    def test_resource_upgrade_api(self, data, code, msg, file_=False, side_effect=None, error=False):

        # Mock update method
        views.upgrade_resource = MagicMock(name='upgrade_resource')

        if side_effect:
            side_effect(self)

        content = json.dumps(data)
        content_type = 'application/json'

        if file_:
            f = StringIO()
            f.name = 'test_file.txt'
            f.write('test file')
            content = {
                'json': json.dumps(data),
                'file': f
            }
            content_type = MULTIPART_CONTENT

        request = self.factory.post(
            '/api/offering/resources/test_user/test_resource/1.0',
            content,
            content_type=content_type,
            HTTP_ACCEPT='application/json'
        )
        request.user = self.user

        res_entry = views.ResourceEntry(permitted_methods=('PUT', 'POST', 'DELETE'))
        response = res_entry.create(request, 'test_user', 'test_resource', '1.0')

        self.assertEqual(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], msg)

        if not error:
            if not file_:
                views.upgrade_resource.assert_called_once_with(self.resource, data)
            else:
                expected_file = request.FILES['file']  # The type change when loaded
                views.upgrade_resource.assert_called_once_with(self.resource, data, expected_file)
            self.assertEqual(body_response['result'], 'correct')
        else:
            self.assertEqual(body_response['result'], 'error')

    @parameterized.expand([
        (204, 'No Content'),
        (404, 'Resource not found', _not_found, True),
        (403, 'Forbidden', _no_provider, True),
        (400, 'Exception in call', _exception_delete, True)
    ])
    def test_resource_deletion_api(self, code, msg, side_effect=None, error=False):

        # Mock delete resource method
        views.delete_resource = MagicMock(name='delete_resource')

        if side_effect:
            side_effect(self)

        request = self.factory.delete(
            '/api/offering/resources/test_user/test_resource/1.0',
            HTTP_ACCEPT='application/json'
        )
        request.user = self.user

        res_entry = views.ResourceEntry(permitted_methods=('POST', 'DELETE'))
        response = res_entry.delete(request, 'test_user', 'test_resource', '1.0')

        self.assertEqual(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], msg)

        if not error:
            views.delete_resource.assert_called_once_with(self.resource)
            self.assertEqual(body_response['result'], 'correct')
        else:
            self.assertEqual(body_response['result'], 'error')


class PublishEntryTestCase(TestCase):

    tags = ('offering-api',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        self.data = {
            'marketplaces': []
        }
        self.request = self.factory.post(
            '/offering/offerings/test_user/test_offering/1.0',
            json.dumps(self.data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.request.user = self.user

    def test_publish_offering(self):

        # Mock publish offering method
        views.publish_offering = MagicMock(name='publish_offering')
        publish_entry = views.PublishEntry(permitted_methods=('POST',))

        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=Organization.objects.get(name=self.user.username),
            owner_admin_user=self.user,
            version='1.0',
            state='uploaded',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )

        # Call the view
        site = Site.objects.create(name='Test_site', domain='http://testsite.com')
        Context.objects.create(site=site)
        views.get_current_site = MagicMock()
        views.get_current_site.return_value = site

        response = publish_entry.create(self.request, 'test_user', 'test_offering', '1.0')

        views.publish_offering.assert_called_once_with(offering, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'OK')
        self.assertEqual(body_response['result'], 'correct')

    def test_publish_offering_not_found(self):

        # Mock publish offering method
        views.publish_offering = MagicMock(name='publish_offering')
        publish_entry = views.PublishEntry(permitted_methods=('POST',))

        # Call the view
        response = publish_entry.create(self.request, 'test_user', 'test_offering', '1.0')

        self.assertFalse(views.publish_offering.called)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Offering not found')
        self.assertEqual(body_response['result'], 'error')

    def test_publish_entry_not_owner(self):

        # Mock publish offering method
        views.publish_offering = MagicMock(name='publish_offering')
        publish_entry = views.PublishEntry(permitted_methods=('POST',))
        org = Organization.objects.get(name=self.user.username)
        org.managers = []
        org.save()

        Offering.objects.create(
            name='test_offering',
            owner_organization=org,
            owner_admin_user=self.user,
            version='1.0',
            state='uploaded',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )
        Offering.is_owner = MagicMock()
        Offering.is_owner.return_value = False

        # Call the view
        response = publish_entry.create(self.request, 'test_user', 'test_offering', '1.0')

        self.assertFalse(views.publish_offering.called)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Forbidden')
        self.assertEqual(body_response['result'], 'error')

    def test_publish_entry_bad_gateway(self):

        # Mock publish offering method
        views.publish_offering = MagicMock(name='publish_offering')
        views.publish_offering.side_effect = HTTPError('', 500, '', None, None)
        publish_entry = views.PublishEntry(permitted_methods=('POST',))

        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=Organization.objects.get(name=self.user.username),
            owner_admin_user=self.user,
            version='1.0',
            state='uploaded',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )
        # Call the view
        response = publish_entry.create(self.request, 'test_user', 'test_offering', '1.0')

        views.publish_offering.assert_called_once_with(offering, self.data)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Bad gateway')
        self.assertEqual(body_response['result'], 'error')

    def test_publish_entry_exception(self):

        # Mock publish offering method
        views.publish_offering = MagicMock(name='publish_offering')
        views.publish_offering.side_effect = Exception('Publication error')
        publish_entry = views.PublishEntry(permitted_methods=('POST',))

        offering = Offering.objects.create(
            name='test_offering',
            owner_organization=Organization.objects.get(name=self.user.username),
            owner_admin_user=self.user,
            version='1.0',
            state='uploaded',
            description_url='',
            resources=[],
            comments=[],
            tags=[],
            image_url='',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date='2013-06-03 10:00:00'
        )
        # Call the view
        response = publish_entry.create(self.request, 'test_user', 'test_offering', '1.0')

        views.publish_offering.assert_called_once_with(offering, self.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Publication error')
        self.assertEqual(body_response['result'], 'error')


class ApplicationCollectionTestCase(TestCase):

    tags = ('fiware-ut-23',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        self.request = self.factory.get(
            '/offering/applications',
            HTTP_ACCEPT='application/json'
        )
        self.request.user = self.user

    def _test_call(self, refresh=False):
        # Mock server calls
        views.urllib2 = MagicMock()

        mock_response = MagicMock()

        response_data = [{
            'id': 1,
            'name': 'test_app1',
            'roles': []
        }, {
            'id': 2,
            'name': 'test_app2',
            'roles': []
        }]

        opener = MagicMock()

        if not refresh:
            mock_response.read.return_value = json.dumps(response_data)

            # Mock urllib openers
            opener.open.return_value = mock_response
            views.urllib2.build_opener.return_value = opener

        else:
            # Create a mock opener able to raise an exception
            # or a response depending on the url
            class fake_opener:

                def open(self, request):
                    url = request.get_full_url()
                    if url.endswith('aaa'):
                        raise HTTPError('', 401, '', None, None)
                    else:
                        mock_response.read.return_value = json.dumps(response_data)
                        return mock_response

            # Mock social auth methods
            UserSocialAuth.refresh_token = MagicMock()
            user_social_auth = UserSocialAuth.objects.create(user=self.request.user, provider='fiware')

            user_social_auth.extra_data = {
                'access_token': 'bbb',
                'refresh_token': 'ccc'
            }

            user_social_auth.save()
            self.request.user.social_auth = [user_social_auth]

            views.urllib2.build_opener.return_value = fake_opener()

        applications_collection = views.ApplicationCollection(permitted_methods=('GET',))
        response = applications_collection.read(self.request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-type'), 'application/json;charset=UTF-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), list)
        self.assertEqual(len(body_response), 2)
        self.assertEqual(body_response[0]['id'], 1)
        self.assertEqual(body_response[0]['name'], 'test_app1')
        self.assertEqual(body_response[1]['id'], 2)
        self.assertEqual(body_response[1]['name'], 'test_app2')

    def test_get_applications(self):

        # Load specific user info
        self.request.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.request.user.userprofile.get_current_roles.return_value = ['provider']
        self.request.user.userprofile.is_user_org = MagicMock(name='is_user_org')
        self.request.user.userprofile.is_user_org.return_value = True
        self.request.user.userprofile.actor_id = 1
        self.request.user.userprofile.access_token = 'aaa'

        self.request.user.userprofile.save()
        self._test_call()

    def test_get_application_organization(self):

        # Load specific user info
        self.request.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.request.user.userprofile.get_current_roles.return_value = ['provider']
        self.request.user.userprofile.is_user_org = MagicMock(name='is_user_org')
        self.request.user.userprofile.is_user_org.return_value = False
        self.request.user.userprofile.current_organization.actor_id = 1
        self.request.user.userprofile.access_token = 'aaa'

        self.request.user.userprofile.save()
        self._test_call()

    def test_get_applications_refresh_token(self):

        # Load specific user info
        self.request.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.request.user.userprofile.get_current_roles.return_value = ['provider']
        self.request.user.userprofile.is_user_org = MagicMock(name='is_user_org')
        self.request.user.userprofile.is_user_org.return_value = True
        self.request.user.userprofile.actor_id = 1
        self.request.user.userprofile.access_token = 'aaa'
        self.request.user.userprofile.refresh_token = 'aaa'

        self.request.user.userprofile.save()
        self._test_call(refresh=True)

    def test_get_applications_exceptions(self):

        self.request.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.request.user.userprofile.get_current_roles.return_value = ['customer']
        self.request.user.userprofile.is_user_org = MagicMock(name='is_user_org')
        self.request.user.userprofile.is_user_org.return_value = True

        applications_collection = views.ApplicationCollection(permitted_methods=('GET',))
        response = applications_collection.read(self.request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        self.assertEqual(body_response['message'], 'Forbidden')
        self.assertEqual(body_response['result'], 'error')
