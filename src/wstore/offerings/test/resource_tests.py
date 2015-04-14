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

import base64
import os
import wstore
from StringIO import StringIO
from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.offerings import resources_management
from wstore.models import Resource
from django.core.exceptions import PermissionDenied
from wstore.store_commons.errors import ConflictError


__test__ = False


RESOURCE_DATA1 = {
    'name': 'Resource1',
    'version': '1.0',
    'description': 'Test resource 1',
    'content_type': 'text/plain',
    'state': 'created',
    'open': False,
    'link': 'http://localhost/media/resources/resource1',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_DATA2 = {
    'name': 'Resource2',
    'version': '2.0',
    'description': 'Test resource 2',
    'content_type': 'text/plain',
    'state': 'created',
    'open': False,
    'link': 'http://localhost/media/resources/resource2',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_DATA3 = {
    'name': 'Resource3',
    'version': '2.0',
    'description': 'Test resource 3',
    'content_type': 'text/plain',
    'state': 'created',
    'open': True,
    'link': 'http://localhost/media/resources/resource3',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_DATA4 = {
    'name': 'Resource4',
    'version': '1.0',
    'description': 'Test resource 4',
    'content_type': 'text/plain',
    'state': 'used',
    'open': True,
    'link': 'http://localhost/media/resources/resource4',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_IN_USE_DATA = {
    'description': 'Test resource 4',
}

RESOURCE_CONTENT = {
    'content': {
        'name': 'test_usdl.rdf',
        'data': ''
    },
}


class FakePlugin():
    pass


class ResourceRegisteringTestCase(TestCase):

    tags = ('fiware-ut-3',)
    fixtures = ['reg_res.json']

    @classmethod
    def tearDownClass(cls):
        reload(wstore.offerings.resource_plugins.decorators)
        reload(resources_management)

    def _basic_encoder(self, data):
        f = open(settings.BASEDIR + '/wstore/test/test_usdl.rdf')
        encoded = base64.b64encode(f.read())
        f.close()
        data['content']['data'] = encoded

    def _fill_provider(self, data):
        res = Resource.objects.filter(name=data['name'])
        provider = User.objects.get(username='test_user')
        for resource in res:
            resource.provider = provider.userprofile.current_organization
            resource.save()

    @parameterized.expand([
        ({
            'name': 'Download',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'content': {
                'name': 'test_usdl.rdf',
                'data': ''
            },
            'resource_type': 'Downloadable',
            'content_type': 'application/rdf+xml'
        }, _basic_encoder),
        ({
            'name': 'History Mod',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'resource_type': 'Downloadable',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        },),
        ({
            'name': 'History Mod',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'resource_type': 'Downloadable',
            'content_type': 'text/plain'
        }, None, True),
        ({
            'name': 'Existing',
            'version': '1.0',
            'description': '',
            'resource_type': 'Downloadable',
            'link': 'https://existing.com/download'
        }, _fill_provider, False, ConflictError, 'The resource Existing already exists. Please upgrade the resource if you want to provide new content'),
        ({
            'name': 'Invalid',
            'version': '1.0a',
            'description': '',
            'resource_type': 'Downloadable',
            'content_type': 'text/plain',
            'link': 'https://existing.com/download'
        }, None, False, ValueError, 'Invalid version format'),
        ({
            'name': 'invalidname$',
            'version': '1.0',
            'description': '',
            'resource_type': 'Downloadable',
            'link': 'https://existing.com/download',
            'content_type': 'text/plain'
        }, None, False, ValueError, 'Invalid name format'),
        ({
            'name': 'InvalidURL',
            'version': '1.0',
            'description': '',
            'resource_type': 'Downloadable',
            'link': 'not an uri',
            'content_type': 'text/plain'
        }, None, False, ValueError, 'Invalid resource link format'),
        ({
            'name': 'Download',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'content': {
                'name': 'test_usd$&.rdf',
                'data': ''
            },
            'resource_type': 'Downloadable',
            'content_type': 'application/rdf+xml'
        }, _basic_encoder, False, ValueError, 'Invalid file name format: Unsupported character'),
        ({
            'version': '1.1',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'resource_type': 'Downloadable',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        }, None, False, ValueError, 'Invalid request: Missing required field'),
        ({
            'name': 'Download',
            'version': '1.1',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'resource_type': 'Downloadable',
            'content_type': 'text/plain'
        }, None, False, ValueError, 'Invalid request: Missing resource content'),
    ])
    def test_resource_registering(self, data, encoder=None, is_file=False, err_type=None, err_msg=None):

        # Call the encoder for the data if needed
        if encoder:
            encoder(self, data)

        f1 = None
        if is_file:
            f = open(settings.BASEDIR + '/wstore/test/test_usdl.rdf')
            f1 = StringIO(f.read())
            f.close()
            f1.name = 'test_usdl.rdf'

        # Build the provider
        provider = User.objects.get(username='test_user')

        # Call the method
        error = None
        try:
            resources_management.register_resource(provider, data, file_=f1)
        except Exception as e:
            error = e

        # Check result
        if not err_type:
            self.assertEquals(error, None)
            res = Resource.objects.get(name=data['name'], version=data['version'])
            self.assertEquals(res.version, data['version'])
            self.assertEquals(res.content_type, data['content_type'])

            if 'content' in data or is_file:
                if is_file:
                    f_name = f1.name
                else:
                    f_name = data['content']['name']

                self.assertEquals(res.resource_path, '/media/resources/' + 'test_user__' + data['name'] + '__' + data['version'] + '__' + f_name)
                res_path = settings.BASEDIR + res.resource_path
                os.remove(res_path)
            elif 'link' in data:
                self.assertEquals(res.download_link, data['link'])
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)

    def _not_existing_plugin(self, data):
        data['resource_type'] = 'not_existing'

    def _url_format(self, data):
        del(data['content'])
        data['link'] = 'http://resourcelink.com'

    def _change_type(self, data):
        data['resource_type'] = 'test_plugin2'

    def _invalid_media(self, data):
        data['content_type'] = 'inv_type'

    def _change_type_api(self, data):
        self._basic_encoder(data)
        data['resource_type'] = 'API'

    @parameterized.expand([
        ('file_format', _basic_encoder),
        ('not_existing', _not_existing_plugin, ValueError, 'Invalid request: The specified resource type is not registered'),
        ('invalid_format_url', _url_format, ValueError, 'Invalid plugin format: URL not allowed for the resource type'),
        ('invalid_format_file', _change_type, ValueError, 'Invalid plugin format: File not allowed for the resource type'),
        ('invalid_media_type', _invalid_media, ValueError, 'Invalid media type: inv_type is not allowed for the resource type'),
        ('invalid_api_format', _change_type_api, ValueError, 'Invalid plugin format: File not allowed for the resource type')
    ])
    def test_resource_registering_plugin(self, name, encoder=None, err_type=None, err_msg=None):

        data = {
            'name': 'Download',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'content': {
                'name': 'test_usdl.rdf',
                'data': ''
            },
            'resource_type': 'test_plugin',
            'content_type': 'application/x-widget'
        }

        # Create plugin module mocks
        plugin_mock = MagicMock(name="test_plugin")
        wstore.offerings.resource_plugins.decorators.load_plugin_module = MagicMock(name="load_plugin_module")
        wstore.offerings.resource_plugins.decorators.load_plugin_module.return_value = plugin_mock
        reload(resources_management)

        if encoder is not None:
            encoder(self, data)

        provider = User.objects.get(username='test_user')

        error = None
        try:
            resources_management.register_resource(provider, data)
        except Exception as e:
            error = e

        if err_type is None:
            self.assertEquals(error, None)
            # Check event calls
            expected_data = {
                'name': 'Download',
                'meta': {},
                'content_path': '/media/resources/test_user__Download__1.0__test_usdl.rdf',
                'version': '1.0',
                'link': '',
                'content_type': 'application/x-widget',
                'open': False,
                'resource_type': 'test_plugin',
                'description': 'This service is in charge of maintaining historical info for Smart Cities'
            }
            plugin_mock.on_pre_create.assert_called_once_with(provider.userprofile.current_organization, expected_data)

            res = Resource.objects.get(name=data['name'], version=data['version'])
            plugin_mock.on_post_create.assert_called_once_with(res)

        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)

    def test_load_plugin_module(self):
        module = 'wstore.offerings.test.resource_tests.FakePlugin'
        from wstore.offerings.resource_plugins.decorators import load_plugin_module

        loaded_module = load_plugin_module(module)

        # Check loaded module
        self.assertTrue(isinstance(loaded_module, FakePlugin))


class ResourceRetrievingTestCase(TestCase):

    tags = ('fiware-ut-3', )

    def setUp(self):
        # Mock resource model
        resource1 = MagicMock()
        resource1.name = 'Resource1'
        resource1.version = '1.0'
        resource1.description = 'Test resource 1'
        resource1.content_type = 'text/plain'
        resource1.state = 'created'
        resource1.open = False
        resource1.get_url.return_value = 'http://localhost/media/resources/resource1'
        resource1.resource_type = 'API'
        resource1.meta_info = {}

        resource2 = MagicMock()
        resource2.name = 'Resource2'
        resource2.version = '2.0'
        resource2.description = 'Test resource 2'
        resource2.content_type = 'text/plain'
        resource2.state = 'created'
        resource2.open = False
        resource2.get_url.return_value = 'http://localhost/media/resources/resource2'
        resource2.resource_type = 'API'
        resource2.meta_info = {}

        resource3 = MagicMock()
        resource3.name = 'Resource3'
        resource3.version = '2.0'
        resource3.description = 'Test resource 3'
        resource3.content_type = 'text/plain'
        resource3.state = 'created'
        resource3.open = True
        resource3.get_url.return_value = 'http://localhost/media/resources/resource3'
        resource3.resource_type = 'API'
        resource3.meta_info = {}

        resource4 = MagicMock()
        resource4.name = 'Resource4'
        resource4.version = '1.0'
        resource4.description = 'Test resource 4'
        resource4.content_type = 'text/plain'
        resource4.state = 'created'
        resource4.open = True
        resource4.get_url.return_value = 'http://localhost/media/resources/resource4'
        resource4.resource_type = 'API'
        resource4.offerings = ['1111', '2222']
        resource4.meta_info = {}

        resources_management.Resource = MagicMock()

        def resource_filter(provider=None, open=None):
            if provider != self.org:
                return []

            if open is None:
                result = [
                    resource1,
                    resource2,
                    resource3,
                    resource4
                ]
            elif not open:
                result = [
                    resource1,
                    resource2
                ]
            else:
                result = [
                    resource3,
                    resource4
                ]
            return result

        resources_management.Resource.objects.filter = resource_filter

        self.user = MagicMock()
        self.org = MagicMock()
        self.user.userprofile.current_organization = self.org

    @classmethod
    def tearDownClass(cls):
        # Restore resource model
        reload(resources_management)
        super(ResourceRetrievingTestCase, cls).tearDownClass()

    @parameterized.expand([
        ([RESOURCE_DATA1, RESOURCE_DATA2, RESOURCE_DATA3, RESOURCE_DATA4],),
        ([RESOURCE_DATA3, RESOURCE_DATA4], True),
        ([RESOURCE_DATA1, RESOURCE_DATA2], False),
        ([RESOURCE_DATA1], None, {"start": 1, "limit": 1}),
        ([RESOURCE_DATA2, RESOURCE_DATA3], None, {"start": 2, "limit": 2}),
        ([RESOURCE_DATA3, RESOURCE_DATA4], None, {"start": 3, "limit": 8}),
        ([], None, {"start": 6}, ValueError, "Missing required parameter in pagination"),
        ([], None, {"limit": 8}, ValueError, "Missing required parameter in pagination"),
        ([], None, {"start": 0, "limit": 8}, ValueError, "Invalid pagination limits"),
        ([], None, {"start": 2, "limit": 0}, ValueError, "Invalid pagination limits"),
        ([], None, {"start": 6, "limit": -1}, ValueError, "Invalid pagination limits"),
        ([], None, {"start": -6, "limit": 2}, ValueError, "Invalid pagination limits"),
        ([], None, {"start": 0, "limit": 0}, ValueError, "Invalid pagination limits")
    ])
    def test_resource_retrieving(self, expected_result, filter_=None, pagination=None, err_type=None, err_msg=None):

        # Call the method
        error = None
        try:
            result = resources_management.get_provider_resources(self.user, filter_, pagination)
        except Exception as e:
            error = e

        if not err_type:
            # Assert that no error occurs
            self.assertEquals(error, None)
            # Check result
            self.assertEquals(result, expected_result)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


class ResourceDeletionTestCase(TestCase):

    tags = ('fiware-ut-3', )

    def setUp(self):
        self.resource = MagicMock()
        self.resource.pk = '4444'
        self.resource.resource_type = 'API'
        resources_management.Offering = MagicMock()

    @classmethod
    def tearDownClass(cls):
        reload(os)
        reload(wstore.offerings.resource_plugins.decorators)
        reload(resources_management)
        super(ResourceDeletionTestCase, cls).tearDownClass()

    def _res_in_use(self):

        def _mock_get(pk=None):
            result = MagicMock()
            if pk == '1111':
                result.state = 'published'
                result.pk = '1111'
            else:
                result.state = 'uploaded'
                result.pk = '2222'
            return result

        resources_management.Offering.objects.get = _mock_get
        resources_management.ObjectId = MagicMock()
        self.resource.offerings = ['1111', '2222']

    def _res_in_use_uploaded(self):
        def _mock_get_up(pk=None):
            result = MagicMock()
            result.state = 'uploaded'
            if pk == '1111':
                result.pk = '1111'
            else:
                result.pk = '2222'
            return result

        resources_management.Offering.objects.get = _mock_get_up
        resources_management.ObjectId = MagicMock()
        self.resource.offerings = ['1111', '2222']
        self.resource.resource_path = '/media/resources/test_resource'
        # Mock delete method
        os.remove = MagicMock()

    def _check_in_use(self):
        self.assertEquals(self.resource.offerings, ['1111'])
        self.assertEquals(self.resource.state, 'deleted')
        self.resource.save.assert_called_once_with()

    def _res_file(self):
        self.resource.offerings = []
        self.resource.resource_path = '/media/resources/test_resource'
        # Mock delete method
        os.remove = MagicMock()

    def _check_deleted(self):
        os.remove.assert_called_once_with(os.path.join(settings.BASEDIR, 'media/resources/test_resource'))
        self.resource.delete.assert_called_once_with()

    def _check_events(self):
        self.plugin_mock.on_pre_delete.assert_called_once_with(self.resource)
        self.plugin_mock.on_post_delete.assert_called_once_with(self.resource)

    def _res_url(self):
        self.resource.offerings = []
        self.resource.resource_path = ''
        # Mock delete method
        os.remove = MagicMock()

    def _check_url(self):
        os.remove.assert_not_called()
        self.resource.delete.assert_called_once_with()

    def _deleted_res(self):
        self.resource.state = 'deleted'

    def _res_plugin(self):
        self.resource.resource_type = 'test_plugin'

        # Create plugin module mocks
        self.plugin_mock = MagicMock(name="test_plugin")
        wstore.offerings.resource_plugins.decorators._get_plugin_model = MagicMock(name="_get_plugin_model")
        wstore.offerings.resource_plugins.decorators.load_plugin_module = MagicMock(name="load_plugin_module")
        wstore.offerings.resource_plugins.decorators.load_plugin_module.return_value = self.plugin_mock
        reload(resources_management)

    @parameterized.expand([
        (_res_in_use, _check_in_use),
        (_res_in_use_uploaded, _check_deleted),
        (_res_file, _check_deleted),
        (_res_url, _check_url),
        (_res_plugin, _check_events),
        (_deleted_res, None, PermissionDenied, 'The resource is already deleted')
    ])
    def test_resource_deletion(self, res_builder, check=None, err_type=None, err_msg=None):

        res_builder(self)

        error = None
        try:
            resources_management.delete_resource(self.resource)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            # Check calls
            check(self)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


UPDATE_DATA1 = {
    'description': 'Test resource 1',
    'content_type': 'text/plain',
    'open': False
}

UPDATE_DATA2 = {
    'content_type': 'text/plain',
    'open': False
}

class ResourceUpdateTestCase(TestCase):

    tags = ('fiware-ut-3', )

    def setUp(self):
        self.resource = MagicMock()
        self.resource.offerings = []
        self.resource.resource_path = ''
        self.resource.resource_type = 'API'
        resources_management.Resource = MagicMock()
        resources_management.Resource.objects.filter.return_value = []

    @classmethod
    def tearDownClass(cls):
        reload(wstore.offerings.resource_plugins.decorators)
        reload(resources_management)
        reload(os)
        super(ResourceUpdateTestCase, cls).tearDownClass()

    def _res_deleted(self):
        self.resource.state = 'deleted'

    def _res_in_use(self):
        self.resource.offerings = ['111', '222']

    def _res_plugin_type(self):
        self.resource.resource_type = 'test_plugin'
        self.plugin_mock = MagicMock(name="test_plugin")
        wstore.offerings.resource_plugins.decorators._get_plugin_model = MagicMock(name="_get_plugin_model")
        wstore.offerings.resource_plugins.decorators.load_plugin_module = MagicMock(name="load_plugin_module")
        wstore.offerings.resource_plugins.decorators.load_plugin_module.return_value = self.plugin_mock
        reload(resources_management)

    def _invalid_media(self):
        self.resource.resource_type = 'test_plugin'
        self.plugin_mock = MagicMock(name="test_plugin")
        wstore.offerings.resource_plugins.decorators._get_plugin_model = MagicMock(name="_get_plugin_model")

        mock_model = MagicMock(name="ResourcePluginModel")
        mock_model.media_types = ['application/x-widget']

        wstore.offerings.resource_plugins.decorators._get_plugin_model.return_value = mock_model
        reload(resources_management)

    def _check_in_use(self):
        self.assertEquals(self.resource.description, 'Test resource 4')

    def _check_complete(self):
        self.assertEquals(self.resource.description, 'Test resource 1')
        self.assertEquals(self.resource.content_type, 'text/plain')
        self.assertEquals(self.resource.open, False)
        self.assertEquals(self.resource.resource_path, '')

    def _check_description(self):
        self.assertEquals(self.resource.description, 'Modified description')

    def _check_no_description(self):
        self.assertEquals(self.resource.content_type, 'text/plain')
        self.assertEquals(self.resource.open, False)
        self.assertEquals(self.resource.resource_path, '')

    def _check_plugin_type(self):
        self._check_complete()
        # Check event calls
        self.plugin_mock.on_pre_update.assert_called_once_with(self.resource)
        self.plugin_mock.on_post_update.assert_called_once_with(self.resource)
        wstore.offerings.resource_plugins.decorators._get_plugin_model.assert_called_once_with('test_plugin')


    @parameterized.expand([
        (RESOURCE_IN_USE_DATA, _check_in_use, _res_in_use),
        (UPDATE_DATA1, _check_complete),
        (UPDATE_DATA2, _check_no_description),
        ({'description': 'Modified description'}, _check_description),
        (UPDATE_DATA1, _check_plugin_type, _res_plugin_type),
        (UPDATE_DATA1, None, _invalid_media, ValueError, 'Invalid media type: text/plain is not allowed for the resource type'),
        ({'name': 'name'}, None, None, ValueError, 'Name field cannot be updated since is used to identify the resource'),
        ({'version': '1.0'}, None, None, ValueError, 'Version field cannot be updated since is used to identify the resource'),
        ({'content_type': 3}, None, None, TypeError, 'Invalid type for content_type field'),
        ({'description': 3}, None, None, TypeError, 'Invalid type for description field'),
        ({'open': 'true'}, None, None, TypeError, 'Invalid type for open field'),
        ({'link': 'http://linktoresoucre.com'}, None, None, ValueError, 'Resource contents cannot be updated. Please upgrade the resource to provide new contents'),
        (RESOURCE_CONTENT, None, None, ValueError, 'Resource contents cannot be updated. Please upgrade the resource to provide new contents'),
        (RESOURCE_DATA1, None, _res_in_use, PermissionDenied, 'The resource is being used, only description can be modified'),
        ({}, None, _res_deleted, PermissionDenied, 'Deleted resources cannot be updated')
    ])
    def test_resource_update(self, data, check=None, side_effect=None, err_type=None, err_msg=None):

        if side_effect:
            side_effect(self)

        error = None
        try:
            resources_management.update_resource(self.resource, data)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            check(self)
            self.resource.save.assert_called_once_with()

        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


UPGRADE_CONTENT = {
    'version': '1.0',
    'content': {
        'name': 'test_usdl.rdf',
        'data': ''
    },
}

UPGRADE_LINK = {
    'version': '1.0',
    'link': 'http://newlinktoresource.com'
}

UPGRADE_INV_LINK = {
    'version': '1.0',
    'link': 'invalid link'
}

class ResourceUpgradeTestCase(TestCase):

    tags = ('fiware-ut-3', )

    @classmethod
    def setUpClass(cls):
        f = open(settings.BASEDIR + '/wstore/test/test_usdl.rdf')
        cls.content = base64.b64encode(f.read())
        f.seek(0)
        cls.res_file = StringIO(f.read())
        cls.res_file.name = 'test_usdl.rdf'
        f.close()
        super(ResourceUpgradeTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        reload(wstore.offerings.resource_plugins.decorators)
        reload(resources_management)
        super(ResourceUpgradeTestCase, cls).tearDownClass()

    def setUp(self):
        # Build resource mock
        self.resource = MagicMock()
        self.resource.name = 'test_resource'
        org = MagicMock()
        org.name = 'test_org'
        self.resource.provider = org
        self.resource.download_link = ''
        self.resource.resource_path = '/media/resources/test_res1.0.rdf'
        self.resource.resource_type = 'Downloadable'
        self.resource.version = '0.1'
        self.resource.old_versions = []

    def _deleted_res(self):
        self.resource.state = 'deleted'

    def _mock_save_file(self):
        resources_management._save_resource_file = MagicMock()
        resources_management._save_resource_file.return_value = '/media/resources/test_usdl.rdf'

    def _mock_res_plugin(self):
        self.resource.resource_type = 'test_plugin'
        self.plugin_mock = MagicMock(name="test_plugin")
        wstore.offerings.resource_plugins.decorators._get_plugin_model = MagicMock(name="_get_plugin_model")
        self.mock_model = MagicMock()
        self.mock_model.formats = ['FILE']
        wstore.offerings.resource_plugins.decorators._get_plugin_model.return_value = self.mock_model
        wstore.offerings.resource_plugins.decorators.load_plugin_module = MagicMock(name="load_plugin_module")
        wstore.offerings.resource_plugins.decorators.load_plugin_module.return_value = self.plugin_mock

        reload(resources_management)
        self._mock_save_file()

    def _mock_res_api(self):
        self.resource.resource_type = 'API'

    def _mock_file_not_allowed(self):
        self._mock_res_plugin()
        self.mock_model.formats = ["URL"]

    @parameterized.expand([
        (UPGRADE_CONTENT, False, _mock_save_file),
        ({'version': '1.0'}, True, _mock_save_file),
        (UPGRADE_LINK,),
        (UPGRADE_CONTENT, False, _mock_res_plugin),
        (UPGRADE_CONTENT, False, _mock_res_api, ValueError, 'Invalid plugin format: File not allowed for the resource type'),
        (UPGRADE_LINK, False, _mock_res_plugin, ValueError, 'Invalid plugin format: URL not allowed for the resource type'),
        (UPGRADE_CONTENT, False, _mock_file_not_allowed, ValueError, 'Invalid plugin format: File not allowed for the resource type'),
        ({}, False, None, ValueError, 'Missing a required field: Version'),
        ({'version': '1.0a'}, False, None, ValueError, 'Invalid version format'),
        ({'version': '1.0'}, False, _deleted_res, PermissionDenied, 'Deleted resources cannot be upgraded'),
        ({'version': '0.0.1'}, False, None, ValueError, 'The new version cannot be lower that the current version: 0.0.1 - 0.1'),
        ({'version': '0.1'}, False, None, ValueError, 'The new version cannot be lower that the current version: 0.1 - 0.1'),
        ({'version': '1.0'}, False, None, ValueError, 'No resource has been provided'),
        (UPGRADE_INV_LINK, False, None, ValueError, 'Invalid URL format')
    ])
    def test_resource_upgrade(self, data, file_used=False, side_effect=None, err_type=None, err_msg=None):

        if side_effect:
            side_effect(self)

        res_file = None
        if file_used:
            res_file = self.res_file
        elif 'content' in data:
            data['content']['data'] = self.content

        error = None
        try:
            resources_management.upgrade_resource(self.resource, data, res_file)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            # Check new version
            self.assertEquals(self.resource.version, data['version'])
            # Check new resource contents
            if 'link' not in data:
                self.assertEquals(self.resource.resource_path, '/media/resources/test_usdl.rdf')
                self.assertEquals(self.resource.download_link, '')

                file_info = self.res_file
                if not file_used:
                    file_info = {
                        'name': 'test_usdl.rdf',
                        'data': self.content
                    }

                resources_management._save_resource_file.assert_called_once_with(
                    'test_org',
                    'test_resource',
                    '1.0',
                    file_info
                )
            else:
                self.assertEquals(self.resource.resource_path, '')
                self.assertEquals(self.resource.download_link, 'http://newlinktoresource.com')

            self.resource.save.assert_called_once_with()

            # Check old versions
            self.assertEquals(len(self.resource.old_versions), 1)
            old_ver = self.resource.old_versions[0]
            self.assertEquals(old_ver.version, '0.1')
            self.assertEquals(old_ver.resource_path, '/media/resources/test_res1.0.rdf')
            self.assertEquals(old_ver.download_link, '')

            # Check events calls if needed
            if self.resource.resource_type != 'Downloadable':
                self.plugin_mock.on_pre_upgrade.assert_called_once_with(self.resource)
                self.plugin_mock.on_post_upgrade.assert_called_once_with(self.resource)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)
