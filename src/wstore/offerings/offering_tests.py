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

import pymongo
import os
import base64
import json
import rdflib
from mock import MagicMock
from nose_parameterized import parameterized
from datetime import datetime
from bson.objectid import ObjectId

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.offerings import offerings_management
from wstore.store_commons.utils.usdlParser import USDLParser
from wstore.models import UserProfile
from wstore.models import Offering
from wstore.models import Marketplace
from wstore.models import Resource
from wstore.models import Organization


__test__ = False


class FakeRepositoryAdaptor():

    _url = None
    _collection = None

    def __init__(self, url, collection=None):
        self._url = url
        if collection != None:
            self._collection = collection

    def upload(self, cont, data, name=None):
        if name != None:
            url = self._url + self._collection + '/' + name
        else:
            url = self._url
        return url

    def delete(self, ser=None):
        pass

    def download(self, name=None, content_type=None):
        # Read the USDL from the file
        path = os.path.join(settings.BASEDIR, 'wstore/test/')
        f = open(os.path.join(path, 'test_usdl.rdf'), 'rb')
        # Return the content
        return {
            'content_type': 'application/rdf+xml',
            'data': f.read()
        }


class FakeMarketAdaptor():

    def __init__(self, url):
        pass

    def add_service(self, store, info):
        pass

    def delete_service(self, store, ser):
        pass


class FakeUsdlParser():

    def __init__(self, data, ct):
        pass

    def parse(self):
        return {
            'pricing': {
                'price_plans': [{
                    'price_components':[]
                }]
            }
        }


class FakeSearchEngine():

    def __init__(self, path):
        pass

    def create_index(self, offering):
        pass


class FakeOfferingRollback():

    _func = None

    def __init__(self, func):
        self._func = func

    def __call__(self, provider, profile, json_data):
        self._func(provider, profile, json_data)


BASIC_OFFERING = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

BASIC_EXPECTED = {
    'image': '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0'
}

OFFERING_BIGGER_VERSION = {
    'name': 'test_offering',
    'version': '3.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

EXPECTED_BIGGER_VERSION = {
    'image': '/media/test_organization__test_offering__3.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__3.0'
}

OFFERING_WITH_IMAGES = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [{
        'name': 'test_screen1.png',
        'data': ''
    },
    {
        'name': 'test_screen2.png',
        'data': ''
    }],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

EXPECTED_WITH_IMAGES = {
    'image':  '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0',
    'screenshots': [
        '/media/test_organization__test_offering__1.0/test_screen1.png',
        '/media/test_organization__test_offering__1.0/test_screen2.png'
    ]
}

OFFERING_USDL_DATA = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test offering',
        'pricing': {
            'price_model': 'free'
        }
    }
}

OFFERING_USDL_DATA_COMPLETE = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test offering',
        'pricing': {
            'price_model': 'single_payment',
            'price': 5
        },
        'legal': {
            'title': 'legal title',
            'text': 'legal text'
        }
    }
}

OFFERING_URL = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'description_url': 'http://examplerep/v1/test_usdl'
}

EXPECTED_URL = {
    'image': '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://examplerep/v1/test_usdl'
}

OFFERING_APPLICATIONS_RESOURCES = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    },
    'applications': [{
        'name': 'test_app1',
        'url': 'http://test_app1.com',
        'id': 1,
        'description': 'a test application'
    }],
    'resources': [{
        'name': 'test_res',
        'description': 'a test resource'
    }]
}

OFFERING_NOTIFY_URL = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'notification_url': 'http://notification_url.com',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_NOTIFY_DEFAULT = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'notification_url': 'default',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

EXPECTED_NOTIFY_URL = {
    'image': '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0',
    'notification_url': 'http://notification_url.com'
}

OFFERING_INVALID_VERSION = {
    'name': 'test_offering',
    'version': '1.0.',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_INVALID_NAME = {
    'name': '.name',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_INVALID_JSON = {
    'na': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_NOTIFY_URL_INVALID = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'notification_url': 'invalid url',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_EXISTING = {
    'name': 'test_offering_fail',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_NO_USDL = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    }
}

OFFERING_USDL_DATA_INVALID = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'pricing': {
            'price_model': 'free'
        }
    }
}
##############################################################################
############################# Test Cases #####################################
##############################################################################

class OfferingCreationTestCase(TestCase):

    tags = ('fiware-ut-1',)
    _db = None
    _image = None
    _usdl = None
    fixtures = ['create.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        connection = pymongo.MongoClient()
        cls._db = connection.test_database

        settings.OILAUTH = False
        # Capture repository calls
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor
        offerings_management.SearchEngine = FakeSearchEngine
        offerings_management.OfferingRollback = FakeOfferingRollback
        # loads test image
        path = os.path.join(settings.BASEDIR, 'wstore/test/')
        f = open(os.path.join(path, 'test_image.png'), 'rb')
        cls._image = base64.b64encode(f.read())
        # loads test USDL
        f = open(os.path.join(path, 'test_usdl.rdf'), 'rb')
        cls._usdl = f.read()

        super(OfferingCreationTestCase, cls).setUpClass()

    def setUp(self):
        settings.OILAUTH = False

    def _remove_media(self, dir_name):
        try:
            path = os.path.join(settings.MEDIA_ROOT, dir_name)
            files = os.listdir(path)

            for f in files:
                file_path = os.path.join(path, f)
                os.remove(file_path)

            os.rmdir(path)
        except:
            pass

    def tearDown(self):
        # Remove media files
        self._remove_media('test_organization__test_offering__1.0')
        self._remove_media('test_organization__test_offering_fail__1.0')
        self._remove_media('test_organization__test_offering__3.0')

        # Remove offering collection
        self._db.wstore_offering.drop()

    def _create_offering(self, offering_data):
        user = User.objects.get(username='test_user')
        org = Organization.objects.get(name='test_organization')

        # Create an offering
        Offering.objects.create(
            name=offering_data['name'],
            owner_organization=org,
            owner_admin_user=user,
            version=offering_data['version'],
            state='uploaded',
            description_url=offering_data['url'],
            resources=[],
            comments=[],
            tags=[],
            image_url='image',
            related_images=[],
            offering_description={},
            notification_url='',
            creation_date=datetime.now(),
        )

    def _fill_image(self, offering_data):
        offering_data['image']['data'] = self._image
        return offering_data

    def _fill_image_err(self, offering_data):
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['data'] = 'invalid usdl'
        return offering_data

    def _fill_basic_images(self, offering_data):
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['data'] = self._usdl
        return offering_data

    def _fill_screenshots(self, offering_data):
        offering_data['image']['data'] = self._image

        # Load screenshots
        path = os.path.join(settings.BASEDIR, 'wstore/test/')
        f = open(os.path.join(path, 'test_screen1.png'), 'rb')
        image1 = base64.b64encode(f.read())

        f = open(os.path.join(path, 'test_screen2.png'), 'rb')
        image2 = base64.b64encode(f.read())
        f.close()

        screen_shots = []
        for scr in offering_data['related_images']:
            if scr['name'] == 'test_screen1.png':
                scr['data'] = image1
            else:
                scr['data'] = image2

            screen_shots.append(scr)

        offering_data['related_images'] = screen_shots
        offering_data['offering_description']['data'] = self._usdl

        return offering_data

    def _fill_previous_version(self, offering_data):
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['data'] = self._usdl

        self._create_offering({
            'name': offering_data['name'],
            'version': '2.0',
            'url': 'url'
        })
        return offering_data

    def _fill_applications(self, offering_data):
        settings.OILAUTH = True
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['data'] = self._usdl
        offerings_management.bind_resources = MagicMock()
        return offering_data

    def _fill_notification_url(self, offering_data):
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['data'] = self._usdl
        org = Organization.objects.get(name='test_organization')
        org.notification_url = 'http://notification_url.com'
        org.save()

        return offering_data

    def _fill_existing_url(self, offering_data):
        offering_data['image']['data'] = self._image
        self._create_offering({
            'name': 'existing offering',
            'version': '2.0',
            'url': 'http://examplerep/v1/test_usdl'
        })
        return offering_data

    def _serialize(self, type_):
        graph = rdflib.Graph()
        graph.parse(data=self._usdl, format='application/rdf+xml')
        return graph.serialize(format=type_, auto_compact=True)

    def _fill_turtle(self, offering_data):
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['content_type']= 'text/turtle'
        offering_data['offering_description']['data'] = self._serialize('n3')
        return offering_data

    def _fill_json(self, offering_data):
        offering_data['image']['data'] = self._image
        offering_data['offering_description']['content_type']= 'application/json'
        offering_data['offering_description']['data'] = self._serialize('json-ld')
        return offering_data

    @parameterized.expand([
        (BASIC_OFFERING, BASIC_EXPECTED, _fill_json),
        (OFFERING_WITH_IMAGES, EXPECTED_WITH_IMAGES, _fill_screenshots),
        (OFFERING_URL, EXPECTED_URL, _fill_image),
        (OFFERING_BIGGER_VERSION, EXPECTED_BIGGER_VERSION, _fill_previous_version),
        (OFFERING_APPLICATIONS_RESOURCES, BASIC_EXPECTED, _fill_applications),
        (OFFERING_NOTIFY_URL, EXPECTED_NOTIFY_URL, _fill_turtle),
        (OFFERING_NOTIFY_DEFAULT, EXPECTED_NOTIFY_URL, _fill_notification_url),
        (OFFERING_USDL_DATA, BASIC_EXPECTED, _fill_image),
        (OFFERING_USDL_DATA_COMPLETE, BASIC_EXPECTED, _fill_image),
        (OFFERING_INVALID_NAME, None, None, ValueError, 'Invalid name format'),
        (BASIC_OFFERING, None, _fill_previous_version, ValueError, 'A bigger version of the current offering exists'),
        (OFFERING_INVALID_VERSION, None, None, ValueError, 'Invalid version format'),
        (OFFERING_INVALID_JSON, None, _fill_basic_images, ValueError, 'Missing required fields'),
        (BASIC_OFFERING, None, _fill_image_err, Exception, 'Malformed USDL'),
        (OFFERING_EXISTING, None, _fill_basic_images, Exception, 'The offering already exists'),
        (OFFERING_NOTIFY_DEFAULT, None, _fill_basic_images, ValueError, 'No default URL defined for the organization'),
        (OFFERING_NOTIFY_URL_INVALID, None, _fill_basic_images, ValueError, "Invalid notification URL format: It doesn't seem to be an URL"),
        (OFFERING_URL, None, _fill_existing_url, ValueError, 'The provided USDL description is already registered'),
        (OFFERING_NO_USDL, None, _fill_image, Exception, 'No USDL description provided'),
        (OFFERING_USDL_DATA_INVALID, None, _fill_image, Exception, 'Invalid USDL info')
    ])
    def test_offering_creation(self, offering_data, expected_data, data_filler=None, err_type=None, err_msg=None):

        if data_filler:
            data = data_filler(self, offering_data)
        else:
            data = offering_data

        user = User.objects.get(username='test_user')
        org = Organization.objects.get(name='test_organization')
        user.userprofile.current_organization = org
        user.userprofile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        user.userprofile.save()

        error = None
        try:
            offerings_management.create_offering(user, data)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            # Check offering contents
            content = self._db.wstore_offering.find_one({
                "name": offering_data['name'],
                "version": offering_data["version"]
            })
            self.assertEqual(content['name'], offering_data['name'])
            self.assertEqual(content['version'], offering_data['version'])
            self.assertEqual(content['state'], 'uploaded')
            self.assertEqual(content['image_url'], expected_data['image'])
            self.assertEqual(content['description_url'], expected_data['description_url'])

            if 'screenshots' in expected_data:
                self.assertEquals(content['related_images'], expected_data['screenshots'])

            if 'applications' in offering_data:
                self.assertEquals(content['applications'], offering_data['applications'])

            if 'resources' in offering_data:
                off = Offering.objects.get(name=offering_data['name'], version=offering_data['version'])
                offerings_management.bind_resources.assert_called_once_with(off, offering_data['resources'], user)

            if 'notification_url' in offering_data:
                self.assertEquals(content['notification_url'], expected_data['notification_url'])
        else:
            self.assertEquals(unicode(error), err_msg)
            self.assertTrue(isinstance(error, err_type))


class OfferingCountTestCase(TestCase):

    tags = ('count',)

    @classmethod
    def setUpClass(cls):
        cls.user = MagicMock()
        cls.org = MagicMock()
        cls.user.userprofile.current_organization = cls.org
        super(OfferingCountTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        reload(offerings_management)
        super(OfferingCountTestCase, cls).tearDownClass()

    def setUp(self):
        offerings_management.Offering = MagicMock()
        count_mock = MagicMock()
        count_mock.count.return_value = 2
        offerings_management.Offering.objects.filter.return_value = count_mock

    def _user_purchased(self):
        self._purchased()
        self.user.userprofile.is_user_org.return_value = True
        self.user.userprofile.offerings_purchased = ['444']

    def _purchased(self):
        self.user.userprofile.is_user_org.return_value = False
        self.user.userprofile.current_organization.offerings_purchased = ['111', '222', '333']

    @parameterized.expand([
        (None, 2, True, 'uploaded'),
        (None, 2, True, 'all'),
        (None, 2, True, 'published'),
        (_purchased, 3, True, 'purchased'),
        (_user_purchased, 4, True, 'purchased'),
        (None, 0, True, 'invalid', ValueError, 'Filter not allowed'),
        (None, 2, False, 'published'),
        (None, 0, False, 'uploaded', ValueError, 'Filter not allowed')
    ])
    def test_count_offerings(self, side_effect, expected_count, owned, filter_, err_type=None, err_msg=None):

        if side_effect:
            side_effect(self)

        error = None
        try:
            return_value = offerings_management.count_offerings(self.user, filter_, owned)
        except Exception as e:
            error = e

        if not err_type:
            self.assertFalse(error)
            self.assertEquals(return_value['number'], expected_count)

            if owned:
                if filter_ == 'uploaded' or filter_ == 'published':
                    offerings_management.Offering.objects.filter.assert_called_once_with(owner_admin_user=self.user, state=filter_, owner_organization=self.org)
                elif filter_ == 'all':
                    offerings_management.Offering.objects.filter.assert_called_once_with(owner_admin_user=self.user, owner_organization=self.org)
            else:
                offerings_management.Offering.objects.filter.assert_called_once_with(state=filter_)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)


class RemoveMock():
    calls = []

    def __call__(self, path):
        self.calls.append(path)

    def assertCall(self, path):
        assert path in self.calls

class OfferingUpdateTestCase(TestCase):

    tags = ('update',)
    fixtures = ['update.json']
    _usdl = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(settings.BASEDIR, 'wstore/test/')
        cls.test_dir = os.path.join(path, 'test_organization__test_offering2__1.0')
        # Create test offering media dir
        os.makedirs(cls.test_dir)

        # loads test USDL
        f = open(os.path.join(path, 'test_usdl.rdf'), 'rb')
        cls._usdl = f.read()
        super(OfferingUpdateTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        reload(os)
        try:
            for file_ in os.listdir(cls.test_dir):
                file_path = os.path.join(cls.test_dir, file_)
                os.remove(file_path)
        except:
            pass
        os.rmdir(cls.test_dir)
        super(OfferingUpdateTestCase, cls).tearDownClass()

    def setUp(self):
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor
        offerings_management.SearchEngine = MagicMock()
        self.se_object = MagicMock()
        offerings_management.SearchEngine.return_value = self.se_object

    def tearDown(self):
        try:
            for file_ in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, file_)
                os.remove(file_path)
        except:
            pass
        reload(offerings_management)
        settings.MEDIA_ROOT = os.path.join(settings.BASEDIR, 'media')

    def _serialize(self, type_):
        graph = rdflib.Graph()
        graph.parse(data=self._usdl, format='application/rdf+xml')
        return graph.serialize(format=type_, auto_compact=True)

    def _fit_usdl(self, data):
        data['offering_description']['data'] = self._usdl
        return data

    def _publish_offering(self, data):
        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")
        offering.state = 'published'
        offering.save()
        return data

    def _mock_images(self, data):
        offerings_management.os.remove = RemoveMock()
        offerings_management.base64 = MagicMock()
        offerings_management.base64.b64decode.return_value = 'decoded data'
        settings.MEDIA_ROOT = os.path.join(settings.BASEDIR, 'wstore/test/')
        return data

    def _invalid_usdl(self, data):
        offerings_management.validate_usdl = MagicMock()
        offerings_management.validate_usdl.return_value = (False, 'Invalid USDL')
        return data

    def _fit_usdl_n3(self, data):
        data['offering_description']['data'] = self._serialize('n3')
        return data

    def _fit_usdl_json(self, data):
        data['offering_description']['data'] = self._serialize('json-ld')
        return data

    @parameterized.expand([
        ({
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': ''
            }
        }, _fit_usdl),
        ({
            'offering_description': {
                'content_type': 'text/turtle',
                'data': ''
            }
        }, _fit_usdl_n3),
        ({
            'offering_description': {
                'content_type': 'application/json',
                'data': ''
            }
        }, _fit_usdl_json),
        ({
            'description_url':  "http://examplerep/v1/test_usdl"
        },),
        ({
            'image': {
                'name': 'test_logo.png',
                'data': 'encoded data'
            },
            'related_images': [{
                'name': 'test_screen1.png',
                'data': 'encoded_data'
            }]
        }, _mock_images),
        ({
            'offering_info': {
                'description': 'Test offering',
                'pricing': {
                    'price_model': 'single_payment',
                    'price': 5
                },
                'legal': {
                    'title': 'legal title',
                    'text': 'legal text'
                }
            }
        },),
        ({}, _publish_offering, PermissionDenied, 'The offering cannot be edited'),
        ({
            'description_url': {
                'content_type': 'application/rdf+xml',
                'link': 'http://examplerep/v1/invalid'
            }
        }, None, ValueError, 'The provided USDL URL is not valid'),
        ({
            'description_url':  "http://examplerep/v1/test_usdl"
        }, _invalid_usdl, ValueError, 'Invalid USDL'),
        ({
            'offering_info': {
                'pricing': {
                    'price_model': 'single_payment',
                    'price': 5
                }
            }
        }, None, ValueError, 'Invalid USDL info')
    ])
    def test_offering_update(self, initial_data, data_filler=None, err_type=None, err_msg=None):

        if data_filler:
            data = data_filler(self, initial_data)
        else:
            data = initial_data

        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")

        error = None
        try:
            offerings_management.update_offering(offering, data)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)

            new_offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")
            self.se_object.update_index.assert_called_with(offering)

            if 'offering_description' in data or 'description_url' in data or 'offering_info' in data:
                usdl = new_offering.offering_description

                parser = USDLParser(json.dumps(usdl), 'application/json')

                usdl_content = parser.parse()
                self.assertEqual(len(usdl_content['services_included']), 1)
                service = usdl_content['services_included'][0]

                if 'offering_description' in data or 'description_url' in data:
                    self.assertEqual(service['name'], 'Map viewer')
                    self.assertEqual(service['vendor'], 'CoNWeT')

                    self.assertEqual(usdl_content['pricing']['title'], 'Map viewer free use')
                    self.assertEqual(len(usdl_content['pricing']['price_plans']), 1)

                    plan = usdl_content['pricing']['price_plans'][0]
                    self.assertEqual(plan['title'], 'Free use')

                else:
                    self.assertEqual(service['name'], 'test_offering2')

                    self.assertEqual(usdl_content['pricing']['title'], 'test_offering2')
                    self.assertEqual(usdl_content['pricing']['description'], 'Test offering')
                    self.assertEqual(len(usdl_content['pricing']['price_plans']), 1)

                    plan = usdl_content['pricing']['price_plans'][0]
                    self.assertEqual(plan['description'], 'This price plan defines a single payment')

            if 'image' in data:
                # Check deletion of old image
                offerings_management.os.remove.assertCall(os.path.join(settings.BASEDIR, 'wstore/test/test_organization__test_offering2__1.0/image.png'))

                f = open(os.path.join(self.test_dir, data['image']['name']), "rb")
                content = f.read()
                self.assertEquals(content, 'decoded data')
                self.assertEquals(new_offering.image_url, '/media/test_organization__test_offering2__1.0/test_logo.png')

            if 'related_images' in data:

                os.remove.assertCall(os.path.join(settings.BASEDIR, 'wstore/test/test_organization__test_offering2__1.0/screen1.png'))

                for img in data['related_images']:
                    f = open(os.path.join(self.test_dir, img['name']), "rb")
                    content = f.read()
                    self.assertEquals(content, 'decoded data')
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


class OfferingRetrievingTestCase(TestCase):

    tags = ('fiware-ut-2',)
    fixtures = ['get_prov.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.USDLParser = FakeUsdlParser
        super(OfferingRetrievingTestCase, cls).setUpClass()

    def test_get_all_provider_offerings(self):
        user = User.objects.get(username='test_user')
        user_org = Organization.objects.get(name=user.username)

        for off in Offering.objects.all():
            off.owner_organization = user_org
            off.save()

        offerings = offerings_management.get_offerings(user, 'all', owned=True)
        self.assertEqual(len(offerings), 3)

        # Check published offering
        for off in offerings:
            if off['name'] == 'test_offering3':
                self.assertEqual(off['name'], 'test_offering3')
                self.assertEqual(off['version'], '1.0')
                self.assertEqual(off['state'], 'published')
                self.assertEqual(off['owner_organization'], 'test_user')
                self.assertEqual(off['owner_admin_user_id'], 'test_user')
                self.assertEqual(off['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering3__1.0')

                self.assertEqual(len(off['resources']), 1)
                resource = off['resources'][0]

                self.assertEqual(resource['name'], 'test_resource')
                self.assertEqual(resource['description'], 'Example resource')

    def test_get_all_provider_offerings_org(self):
        user = User.objects.get(username='test_user')
        user_org = Organization.objects.get(name=user.username)

        org = Organization.objects.get(name='test_organization')
        user.userprofile.current_organization = org
        user.userprofile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        user.userprofile.save()

        off1 = Offering.objects.get(name='test_offering1')
        off1.owner_organization = user_org
        off1.save()

        off2 = Offering.objects.get(name='test_offering2')
        off2.owner_organization = user_org
        off2.save()

        offerings = offerings_management.get_offerings(user, 'all', owned=True)
        self.assertEqual(len(offerings), 1)

        # Check published offering
        self.assertEqual(offerings[0]['name'], 'test_offering3')
        self.assertEqual(offerings[0]['version'], '1.0')
        self.assertEqual(offerings[0]['state'], 'published')
        self.assertEqual(offerings[0]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[0]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[0]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering3__1.0')

        self.assertEqual(len(offerings[0]['resources']), 1)
        resource = offerings[0]['resources'][0]

        self.assertEqual(resource['name'], 'test_resource')
        self.assertEqual(resource['description'], 'Example resource')

    def test_get_provider_uploaded_offerings(self):

        user = User.objects.get(username='test_user')
        org = Organization.objects.get(name='test_organization')
        user.userprofile.current_organization = org
        user.userprofile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        user.userprofile.save()

        offerings = offerings_management.get_offerings(user, 'uploaded', owned=True)
        self.assertEqual(len(offerings), 2)

        for off in offerings:
            if off['name'] == 'test_offering1':
                self.assertEqual(off['name'], 'test_offering1')
                self.assertEqual(off['version'], '1.0')
                self.assertEqual(off['state'], 'uploaded')
                self.assertEqual(off['owner_organization'], 'test_organization')
                self.assertEqual(off['owner_admin_user_id'], 'test_user')
                self.assertEqual(off['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering1__1.0')
            else:
                self.assertEqual(off['name'], 'test_offering2')
                self.assertEqual(off['version'], '1.1')
                self.assertEqual(off['state'], 'uploaded')
                self.assertEqual(off['owner_organization'], 'test_organization')
                self.assertEqual(off['owner_admin_user_id'], 'test_user')
                self.assertEqual(off['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering2__1.1')


class PurchasedOfferingRetrievingTestCase(TestCase):

    tags = ('fiware-ut-2',)
    fixtures = ['get_purch.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.USDLParser = FakeUsdlParser
        super(PurchasedOfferingRetrievingTestCase, cls).setUpClass()

    def test_get_customer_purchased_offerings(self):

        user = User.objects.get(username='test_user2')
        profile = UserProfile.objects.get(user=user)
        profile.offerings_purchased = ['11000aba8e05ac2115f022f9']
        org = Organization.objects.get(name='test_organization1')
        org.offerings_purchased = ['21000aba8e05ac2115f022ff', '11000aba8e05ac2115f022f9']
        org.save()
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        offerings = offerings_management.get_offerings(user, 'purchased', owned=True)

        self.assertEqual(len(offerings), 2)
        for off in offerings:
            if off['name'] == 'test_offering1':
                self.assertEqual(off['name'], 'test_offering1')
                self.assertEqual(off['version'], '1.0')
                self.assertEqual(off['state'], 'purchased')
                self.assertEqual(off['owner_organization'], 'test_organization')
                self.assertEqual(off['owner_admin_user_id'], 'test_user')
                self.assertEqual(off['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering1__1.0')
                self.assertEqual(len(off['bill']), 1)
                self.assertEqual(off['bill'][0], '/media/bills/61005aba8e05ac2115f022f0.pdf')
                components = off['offering_description']['pricing']['price_plans'][0]['price_components']
                self.assertEqual(components[0]['title'], 'price component 1')
                self.assertEqual(components[0]['renovation_date'], '1990-02-05 17:06:46')
                self.assertEqual(components[1]['title'], 'price component 2')
                self.assertEqual(components[1]['renovation_date'], '1990-02-05 17:06:46')
            else:

                self.assertEqual(off['name'], 'test_offering2')
                self.assertEqual(off['version'], '1.1')
                self.assertEqual(off['state'], 'purchased')
                self.assertEqual(off['owner_organization'], 'test_organization')
                self.assertEqual(off['owner_admin_user_id'], 'test_user')
                self.assertEqual(off['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering2__1.1')
                self.assertEqual(len(off['bill']), 1)
                self.assertEqual(off['bill'][0], '/media/bills/61006aba8e05ac2115f022f0.pdf')
                components = off['offering_description']['pricing']['price_plans'][0]['price_components']
                self.assertEqual(components[0]['title'], 'price component 1')
                self.assertEqual(components[0]['renovation_date'], '1990-02-05 17:06:46')
                self.assertEqual(components[1]['title'], 'price component 2')
                self.assertEqual(components[1]['renovation_date'], '1990-02-05 17:06:46')

    def test_get_published_offerings(self):
        user = User.objects.get(username='test_user2')
        profile = UserProfile.objects.get(user=user)
        profile.offerings_purchased = ['11000aba8e05ac2115f022f9']
        org = Organization.objects.get(name='test_organization1')
        org.offerings_purchased = ['21000aba8e05ac2115f022ff', '11000aba8e05ac2115f022f9']
        org.save()
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        offerings = offerings_management.get_offerings(user)
        self.assertEqual(len(offerings), 3)
        self.assertEqual(offerings[0]['name'], 'test_offering1')
        self.assertEqual(offerings[0]['version'], '1.0')
        self.assertEqual(offerings[0]['state'], 'purchased')
        self.assertEqual(offerings[0]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[0]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[0]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering1__1.0')
        components = offerings[0]['offering_description']['pricing']['price_plans'][0]['price_components']
        self.assertEqual(components[0]['title'], 'price component 1')
        self.assertEqual(components[0]['renovation_date'], '1990-02-05 17:06:46')
        self.assertEqual(components[1]['title'], 'price component 2')
        self.assertEqual(components[1]['renovation_date'], '1990-02-05 17:06:46')

        self.assertEqual(offerings[1]['name'], 'test_offering2')
        self.assertEqual(offerings[1]['version'], '1.1')
        self.assertEqual(offerings[1]['state'], 'purchased')
        self.assertEqual(offerings[1]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[1]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[1]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering2__1.1')
        components = offerings[1]['offering_description']['pricing']['price_plans'][0]['price_components']
        self.assertEqual(components[0]['title'], 'price component 1')
        self.assertEqual(components[0]['renovation_date'], '1990-02-05 17:06:46')
        self.assertEqual(components[1]['title'], 'price component 2')
        self.assertEqual(components[1]['renovation_date'], '1990-02-05 17:06:46')

        self.assertEqual(offerings[2]['name'], 'test_offering3')
        self.assertEqual(offerings[2]['version'], '1.0')
        self.assertEqual(offerings[2]['state'], 'published')
        self.assertEqual(offerings[2]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[2]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[2]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering3__1.0')


class OfferingPaginationTestCase(TestCase):

    tags = ('fiware-ut-2',)
    fixtures = ['get_off_pag.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.USDLParser = FakeUsdlParser
        super(OfferingPaginationTestCase, cls).setUpClass()

    def test_basic_retrieving_pagination(self):

        pagination = {
            'skip': '1',
            'limit': '3'
        }

        user = User.objects.get(username='test_user')
        org = Organization.objects.get(name='test_organization')
        user.userprofile.current_organization = org
        user.userprofile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        user.userprofile.save()
        offerings = offerings_management.get_offerings(user, filter_='all', owned=True, pagination=pagination)

        self.assertEqual(len(offerings), 3)

        self.assertEqual(offerings[0]['name'], 'test_offering1')
        self.assertEqual(offerings[1]['name'], 'test_offering2')
        self.assertEqual(offerings[2]['name'], 'test_offering3')

        pagination = {
            'skip': '4',
            'limit': '5'
        }

        offerings = offerings_management.get_offerings(user, filter_='all', owned=True, pagination=pagination)

        self.assertEqual(len(offerings), 5)

        self.assertEqual(offerings[0]['name'], 'test_offering4')
        self.assertEqual(offerings[1]['name'], 'test_offering5')
        self.assertEqual(offerings[2]['name'], 'test_offering6')
        self.assertEqual(offerings[3]['name'], 'test_offering7')
        self.assertEqual(offerings[4]['name'], 'test_offering8')

    def test_retrieving_pagination_half_page(self):

        pagination = {
            'skip': '8',
            'limit': '10'
        }

        user = User.objects.get(username='test_user')
        org = Organization.objects.get(name='test_organization')
        user.userprofile.current_organization = org
        user.userprofile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        user.userprofile.save()
        offerings = offerings_management.get_offerings(user, filter_='all', owned=True, pagination=pagination, sort='name')

        self.assertEqual(len(offerings), 3)

        self.assertEqual(offerings[0]['name'], 'test_offering7')
        self.assertEqual(offerings[1]['name'], 'test_offering8')
        self.assertEqual(offerings[2]['name'], 'test_offering9')

    def test_retrieving_pagination_invalid_limit(self):
        pagination = {
            'skip': '1',
            'limit': '-2'
        }

        user = User.objects.get(username='test_user')

        error = False
        msg = None

        try:
            offerings_management.get_offerings(user, filter_='all', owned=True, pagination=pagination)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Invalid pagination limits')

    def test_retrieving_pagination_invalid_start(self):
        pagination = {
            'skip': '-4',
            'limit': '2'
        }

        user = User.objects.get(username='test_user')

        error = False
        msg = None

        try:
            offerings_management.get_offerings(user, filter_='all', owned=True, pagination=pagination)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Invalid pagination limits')


class PurchasedOfferingPaginationTestCase(TestCase):

    tags = ('fiware-ut-2',)
    fixtures = ['get_purch_off_pag.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.USDLParser = FakeUsdlParser
        super(PurchasedOfferingPaginationTestCase, cls).setUpClass()

    def test_basic_retrieving_pagination_purchased(self):

        pagination = {
            'skip': '1',
            'limit': '2'
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        profile.offerings_purchased = ['11000aba8e05ac2115f022f9', '21000aba8e05ac2115f022ff', '31000aba8e05ac2115f022f0']
        org = Organization.objects.get(name='test_organization1')
        org.offerings_purchased = ['41000aba8e05ac2115f022f0', '51100aba8e05ac2115f022f0']
        org.save()
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        offerings = offerings_management.get_offerings(user, filter_='purchased', owned=True, pagination=pagination, sort='name')

        self.assertEqual(len(offerings), 2)

        self.assertEqual(offerings[0]['name'], 'test_offering4')
        self.assertEqual(offerings[1]['name'], 'test_offering5')


class OfferingPublicationTestCase(TestCase):

    tags = ('fiware-ut-4',)
    fixtures = ['pub.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        connection = pymongo.MongoClient()
        cls._db = connection.test_database
        offerings_management.MarketAdaptor = FakeMarketAdaptor

        super(OfferingPublicationTestCase, cls).setUpClass()

    def setUp(self):
        offerings_management.SearchEngine = MagicMock()
        self.se_object = MagicMock()
        offerings_management.SearchEngine.return_value = self.se_object

    def test_basic_publication(self):
        data = {
            'marketplaces': []
        }
        offering = Offering.objects.get(name='test_offering1')
        offerings_management.publish_offering(offering, data)

        offering = Offering.objects.get(name='test_offering1')
        self.assertEqual(offering.state, 'published')
        self.se_object.update_index.assert_called_with(offering)

    def test_publication_marketplace(self):
        data = {
            'marketplaces': ['test_market']
        }
        offering = Offering.objects.get(name='test_offering1')
        offerings_management.publish_offering(offering, data)

        offering = Offering.objects.get(name='test_offering1')
        self.assertEqual(offering.state, 'published')
        self.assertEqual(len(offering.marketplaces), 1)
        market = Marketplace.objects.get(pk=offering.marketplaces[0])
        self.assertEqual(market.name, 'test_market')
        self.se_object.update_index.assert_called_with(offering)

    def test_publication_not_existing_marketplace(self):
        data = {
            'marketplaces': ['test_marketplace']
        }
        offering = Offering.objects.get(name='test_offering1')
        error = False
        try:
            offerings_management.publish_offering(offering, data)
        except:
            error = True

        self.assertTrue(error)

    def test_publication_some_marketplaces(self):
        data = {
            'marketplaces': ['test_market', 'test_market2']
        }
        offering = Offering.objects.get(name='test_offering1')
        offerings_management.publish_offering(offering, data)

        offering = Offering.objects.get(name='test_offering1')
        self.assertEqual(offering.state, 'published')
        self.assertEqual(len(offering.marketplaces), 2)
        market = Marketplace.objects.get(pk=offering.marketplaces[0])
        self.assertEqual(market.name, 'test_market')
        market = Marketplace.objects.get(pk=offering.marketplaces[1])
        self.assertEqual(market.name, 'test_market2')

    def test_publication_invalid_JSON(self):
        data = {
            'marketpla': ['test_market']
        }
        offering = Offering.objects.get(name='test_offering1')
        error = False
        try:
            offerings_management.publish_offering(offering, data)
        except:
            error = True

        self.assertTrue(error)


class OfferingBindingTestCase(TestCase):

    tags = ('binding',)
    fixtures = ['bind.json']

    @classmethod
    def setUpClass(cls):
        settings.OILAUTH = False

    def _fill_resources_org(self, data, org):
        try:
            for res in data:
                resource = Resource.objects.get(name=res['name'])
                resource.provider = org
                resource.save()
        except:
            pass

    def _publish_offering(self):
        offering = Offering.objects.get(name='test_offering1')
        offering.state = 'published'
        offering.save()

    def _deleted_resource(self):
        res = Resource.objects.get(name='test_resource1')
        res.state = 'deleted'
        res.save()

    def _resource_not_open(self):
        offering = Offering.objects.get(name='test_offering1')
        offering.open = True
        offering.save()

    def _resource_included(self):
        offering = Offering.objects.get(name='test_offering2')
        res = Resource.objects.get(name='test_resource3')
        offering.resources.append(ObjectId(res.pk))
        offering.save()

    @parameterized.expand([
        ([{
            'name': 'test_resource1',
            'version': '1.0'
        }], 'test_offering1'),
        ([{
            'name': 'test_resource1',
            'version': '1.0'
        },
        {
            'name': 'test_resource3',
            'version': '1.0'
        }], 'test_offering2'),
        ([{
            'name': 'test_resource1',
            'version': '1.0'
        },
        {
            'name': 'test_resource3',
            'version': '1.0'
        }], 'test_offering2', _resource_included),
        ([], 'test_offering2'),
        ([{
            'name': 'test_resource4',
            'version': '1.0'
        }], 'test_offering1', None, ValueError, 'Resource not found: test_resource4 1.0'),
        ([], 'test_offering1', _publish_offering, PermissionDenied, 'This offering cannot be modified'),
        ([{
            'name': 'test_resource1',
            'version': '1.0'
        }], 'test_offering1', _deleted_resource, PermissionDenied, 'Invalid resource, the resource test_resource1 1.0 is deleted'),
        ([{
            'name': 'test_resource1',
            'version': '1.0'
        }], 'test_offering1', _resource_not_open, PermissionDenied, 'It is not allowed to include not open resources in an open offering')
    ])
    def test_binding(self, data, offering_name, side_effect=None, err_type=None, err_msg=None):

        if side_effect:
            side_effect(self)

        offering = Offering.objects.get(name=offering_name)
        provider = User.objects.get(username='test_user')
        org = Organization.objects.get(name=provider.username)

        self._fill_resources_org(data, org)

        error = None
        try:
            offerings_management.bind_resources(offering, data, provider)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            # Refresh offering object
            offering = Offering.objects.get(name=offering_name)
            # Check binding
            self.assertEquals(len(offering.resources), len(data))

            for off_res in offering.resources:
                found = False
                res = Resource.objects.get(pk=off_res)

                for exp_res in data:
                    if res.name == exp_res['name']:
                        self.assertEquals(res.version, exp_res['version'])
                        found = True
                        break
                self.assertTrue(found)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)

class OfferingDeletionTestCase(TestCase):

    tags = ('fiware-ut-5',)
    fixtures = ['del.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.MarketAdaptor = FakeMarketAdaptor
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor
        super(OfferingDeletionTestCase, cls).setUpClass()

    def setUp(self):
        offerings_management.SearchEngine = MagicMock()
        self.se_object = MagicMock()
        offerings_management.SearchEngine.return_value = self.se_object

    def test_delete_uploaded_offering(self):
        offering = Offering.objects.get(name='test_offering')
        # Mock os
        offerings_management.os = MagicMock()
        offerings_management.delete_offering(offering)
        error = False
        try:
            offering = Offering.objects.get(name='test_offering')
        except:
            error = True

        self.assertTrue(error)

    def test_delete_published_offering(self):
        offering = Offering.objects.get(name='test_offering2')
        offerings_management.delete_offering(offering)
        offering = Offering.objects.get(name='test_offering2')
        self.assertEqual(offering.state, 'deleted')
        self.se_object.update_index.assert_called_with(offering)

    def test_delete_published_offering_marketplace(self):
        offering = Offering.objects.get(name='test_offering3')
        offerings_management.delete_offering(offering)
        offering = Offering.objects.get(name='test_offering3')
        self.assertEqual(offering.state, 'deleted')
        self.se_object.update_index.assert_called_with(offering)
