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
from StringIO import StringIO
from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.offerings import resources_management
from wstore.models import Resource
from django.core.exceptions import PermissionDenied


__test__ = False


class ResourceRegisteringTestCase(TestCase):

    tags = ('fiware-ut-3',)
    fixtures = ['reg_res.json']

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
            'content_type': 'application/rdf+xml'
        }, _basic_encoder),
        ({
            'name': 'History Mod',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        },),
        ({
            'name': 'History Mod',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'content_type': 'text/plain'
        }, None, True),
        ({
            'name': 'Existing',
            'version': '1.0',
            'description': '',
            'type': 'download',
            'link': 'https://existing.com/download'
        }, _fill_provider, False, ValueError, 'The resource Existing already exists. Please upgrade the resource if you want to provide new content'),
        ({
            'name': 'Invalid',
            'version': '1.0a',
            'description': '',
            'type': 'download',
            'content_type': 'text/plain',
            'link': 'https://existing.com/download'
        }, None, False, ValueError, 'Invalid version format'),
        ({
            'name': 'invalidname$',
            'version': '1.0',
            'description': '',
            'type': 'download',
            'link': 'https://existing.com/download',
            'content_type': 'text/plain'
        }, None, False, ValueError, 'Invalid name format'),
        ({
            'name': 'InvalidURL',
            'version': '1.0',
            'description': '',
            'type': 'download',
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
            'content_type': 'application/rdf+xml'
        }, _basic_encoder, False, ValueError, 'Invalid file name format: Unsupported character'),
        ({
            'version': '1.1',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        }, None, False, ValueError, 'Invalid request: Missing required field'),
        ({
            'name': 'Download',
            'version': '1.1',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
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


RESOURCE_DATA1 = {
    'name': 'Resource1',
    'version': '1.0',
    'description': 'Test resource 1',
    'content_type': 'text/plain',
    'state': 'created',
    'open': False,
    'link': 'http://localhost/media/resources/resource1'
}

RESOURCE_DATA2 = {
    'name': 'Resource2',
    'version': '2.0',
    'description': 'Test resource 2',
    'content_type': 'text/plain',
    'state': 'created',
    'open': False,
    'link': 'http://localhost/media/resources/resource2'
}

RESOURCE_DATA3 = {
    'name': 'Resource3',
    'version': '2.0',
    'description': 'Test resource 3',
    'content_type': 'text/plain',
    'state': 'created',
    'open': True,
    'link': 'http://localhost/media/resources/resource3'
}

RESOURCE_DATA4 = {
    'name': 'Resource4',
    'version': '1.0',
    'description': 'Test resource 4',
    'content_type': 'text/plain',
    'state': 'used',
    'open': True,
    'link': 'http://localhost/media/resources/resource4',
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

        resource2 = MagicMock()
        resource2.name = 'Resource2'
        resource2.version = '2.0'
        resource2.description = 'Test resource 2'
        resource2.content_type = 'text/plain'
        resource2.state = 'created'
        resource2.open = False
        resource2.get_url.return_value = 'http://localhost/media/resources/resource2'

        resource3 = MagicMock()
        resource3.name = 'Resource3'
        resource3.version = '2.0'
        resource3.description = 'Test resource 3'
        resource3.content_type = 'text/plain'
        resource3.state = 'created'
        resource3.open = True
        resource3.get_url.return_value = 'http://localhost/media/resources/resource3'

        resource4 = MagicMock()
        resource4.name = 'Resource4'
        resource4.version = '1.0'
        resource4.description = 'Test resource 4'
        resource4.content_type = 'text/plain'
        resource4.state = 'created'
        resource4.open = True
        resource4.get_url.return_value = 'http://localhost/media/resources/resource4'
        resource4.offerings = ['1111', '2222']

        resources_management.Resource = MagicMock()
        resources_management.Resource.objects.filter.return_value = [
            resource1,
            resource2,
            resource3,
            resource4
        ]
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
        ([RESOURCE_DATA3, RESOURCE_DATA4], 'true'),
        ([RESOURCE_DATA1, RESOURCE_DATA2], 'false')
    ])
    def test_resource_retrieving(self, expected_result, filter_=None):

        # Call the method
        error = False
        try:
            result = resources_management.get_provider_resources(self.user, filter_)
        except:
            error = True

        # Assert that no error occurs
        self.assertFalse(error)

        # Check calls
        resources_management.Resource.objects.filter.assert_called_once_with(provider=self.org)
        # Check result
        self.assertEquals(result, expected_result)


class ResourceDeletionTestCase(TestCase):

    tags = ('fiware-ut-3', )

    def setUp(self):
        self.resource = MagicMock()
        self.resource.pk = '4444'
        resources_management.Offering = MagicMock()

    @classmethod
    def tearDownClass(cls):
        reload(os)
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

    @parameterized.expand([
        (_res_in_use, _check_in_use),
        (_res_in_use_uploaded, _check_deleted),
        (_res_file, _check_deleted),
        (_res_url, _check_url),
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
        resources_management.Resource = MagicMock()
        resources_management.Resource.objects.filter.return_value = []

    @classmethod
    def tearDownClass(cls):
        reload(resources_management)
        reload(os)
        super(ResourceUpdateTestCase, cls).tearDownClass()

    def _res_deleted(self):
        self.resource.state = 'deleted'

    def _res_in_use(self):
        self.resource.offerings = ['111', '222']

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

    @parameterized.expand([
        (RESOURCE_IN_USE_DATA, _check_in_use, _res_in_use),
        (UPDATE_DATA1, _check_complete),
        (UPDATE_DATA2, _check_no_description),
        ({'description': 'Modified description'}, _check_description),
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
        self.resource.version = '0.1'
        self.resource.old_versions = []

    def _deleted_res(self):
        self.resource.state = 'deleted'

    def _mock_save_file(self):
        resources_management._save_resource_file = MagicMock()
        resources_management._save_resource_file.return_value = '/media/resources/test_usdl.rdf'

    @parameterized.expand([
        (UPGRADE_CONTENT, False, _mock_save_file),
        ({'version': '1.0'}, True, _mock_save_file),
        (UPGRADE_LINK,),
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
            if not 'link' in data:
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
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)
