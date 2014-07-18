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

import base64
import os
from StringIO import StringIO
from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.offerings import resources_management
from wstore.models import Resource, Organization


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
            'name': 'Download',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'content_type': 'application/rdf+xml'
        }, None, True),
        ({
            'name': 'New version resource',
            'version': '2.1',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        }, _fill_provider),
        ({
            'name': 'Existing',
            'version': '1.0',
            'description': '',
            'type': 'download',
            'link': 'https://existing.com/download'
        }, _fill_provider, False, ValueError, 'The resource already exists'),
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
            'name': 'New version resource',
            'version': '1.1',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        }, _fill_provider, False, ValueError, 'A bigger version of the resource exists'),
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
