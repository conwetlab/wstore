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

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.offerings.resources_management import register_resource
from wstore.models import Resource


__test__ = False

class ResourceRegisteringTestCase(TestCase):

    tags = ('fiware-ut-3',)
    fixtures = ['reg_res.json']

    def test_resource_registering_download_encoded(self):

        f = open(settings.BASEDIR + '/wstore/test/test_usdl.rdf')
        encoded = base64.b64encode(f.read())
        f.close()
        data = {
            'name': 'Download',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'content': {
                'name': 'test_usdl.rdf',
                'data': encoded 
            },
            'content_type': 'application/rdf+xml'
        }

        provider = User.objects.get(username='test_user')
        register_resource(provider, data)

        res = Resource.objects.get(name='Download')
        self.assertEqual(res.version, '1.0')
        self.assertEqual(res.resource_path, '/media/resources/test_user__Download__1.0__test_usdl.rdf')

        res_path = settings.BASEDIR + res.resource_path
        os.remove(res_path)

    def test_resource_registering_download_multipart(self):

        f = open(settings.BASEDIR + '/wstore/test/test_usdl.rdf')
        f1 = StringIO(f.read())
        f.close()

        f1.name = 'test_usdl.rdf'

        data = {
            'name': 'Download',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'content_type': 'application/rdf+xml'
        }

        provider = User.objects.get(username='test_user')
        register_resource(provider, data, f1)

        res = Resource.objects.get(name='Download')
        self.assertEqual(res.version, '1.0')
        self.assertEqual(res.resource_path, '/media/resources/test_user__Download__1.0__test_usdl.rdf')

        res_path = settings.BASEDIR + res.resource_path
        os.remove(res_path)

    def test_resource_registering_download_link(self):

        data = {
            'name': 'History Mod',
            'version': '1.0',
            'description': 'This service is in charge of maintaining historical info for Smart Cities',
            'type': 'download',
            'link': 'https://historymod.com/download',
            'content_type': 'text/plain'
        }

        provider = User.objects.get(username='test_user')
        register_resource(provider, data)

        res = Resource.objects.get(name='History Mod')

        self.assertEqual(res.version, '1.0')
        self.assertEqual(res.download_link, 'https://historymod.com/download')
        self.assertEqual(res.content_type, 'text/plain')

    def test_resource_registering_already_existing(self):

        data = {
            'name': 'Existing',
            'version': '1.0',
            'description': '',
            'type': 'download',
            'link': 'https://existing.com/download'
        }

        provider = User.objects.get(username='test_user')

        error = False
        msg = None
        try:
            register_resource(provider, data)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'The resource already exists')

    def test_resource_registering_invalid_version(self):

        data = {
            'name': 'Invalid',
            'version': '1.0a',
            'description': '',
            'type': 'download',
            'link': 'https://existing.com/download'
        }

        provider = User.objects.get(username='test_user')

        error = False
        msg = None
        try:
            register_resource(provider, data)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Invalid version format')