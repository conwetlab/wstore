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

import pymongo
import os
import base64
import json
from mock import MagicMock

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

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

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        # Remove media files
        try:
            dir_name = 'test_organization__test_offering__1.0'
            path = os.path.join(settings.MEDIA_ROOT, dir_name)
            files = os.listdir(path)

            for f in files:
                file_path = os.path.join(path, f)
                os.remove(file_path)

            os.rmdir(path)
            dir_name = 'test_organization__test_offering_fail__1.0'
            path = os.path.join(settings.MEDIA_ROOT, dir_name)
            files = os.listdir(path)

            for f in files:
                file_path = os.path.join(path, f)
                os.remove(file_path)

            os.rmdir(path)
        except:
            pass

        # Remove offering collection
        self._db.wstore_offering.drop()

    def test_create_basic_offering(self):
        """
        Test the basic creation of an offering
        """
        data = {
            'name': 'test_offering',
            'version': '1.0',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [],
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': self._usdl
            }
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        offerings_management.create_offering(user, data)
        content = self._db.wstore_offering.find_one({"name": "test_offering"})

        self.assertEqual(content['name'], 'test_offering')
        self.assertEqual(content['version'], '1.0')
        self.assertEqual(content['state'], 'uploaded')
        self.assertEqual(content['image_url'], '/media/test_organization__test_offering__1.0/test_image.png')
        self.assertEqual(content['description_url'], 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0')

    def test_create_offering_images(self):
        """
        Test the basic creation of an offering
        """
        # load screenshots

        path = os.path.join(settings.BASEDIR, 'wstore/test/')
        f = open(os.path.join(path, 'test_screen1.png'), 'rb')
        image1 = base64.b64encode(f.read())

        f = open(os.path.join(path, 'test_screen2.png'), 'rb')
        image2 = base64.b64encode(f.read())

        data = {
            'name': 'test_offering',
            'version': '1.0',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [{
                'name': 'test_screen1.png',
                'data': image1
            },
            {
                'name': 'test_screen2.png',
                'data': image2
            }],
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': self._usdl
            }
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        offerings_management.create_offering(user, data)
        content = self._db.wstore_offering.find_one({"name": "test_offering"})

        self.assertEqual(content['name'], 'test_offering')
        self.assertEqual(content['version'], '1.0')
        self.assertEqual(content['state'], 'uploaded')
        self.assertEqual(content['image_url'], '/media/test_organization__test_offering__1.0/test_image.png')
        self.assertEqual(content['description_url'], 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0')

        self.assertEqual(len(content['related_images']), 2)
        contains = '/media/test_organization__test_offering__1.0/test_screen1.png' in content['related_images']
        self.assertTrue(contains)
        contains = '/media/test_organization__test_offering__1.0/test_screen2.png' in content['related_images']
        self.assertTrue(contains)

    def test_create_offering_usdl_url(self):

        data = {
            'name': 'test_offering',
            'version': '1.0',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [],
            'description_url': 'http://examplerep/v1/test_usdl'
        }

        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        offerings_management.create_offering(user, data)
        content = self._db.wstore_offering.find_one({"name": "test_offering"})

        self.assertEqual(content['name'], 'test_offering')
        self.assertEqual(content['version'], '1.0')
        self.assertEqual(content['state'], 'uploaded')
        self.assertEqual(content['image_url'], '/media/test_organization__test_offering__1.0/test_image.png')
        self.assertEqual(content['description_url'], 'http://examplerep/v1/test_usdl')

    def test_create_offering_invalid_version(self):
        """
        Test the creating of an offering with invalid version format
        """
        data = {
            'name': 'test_offering',
            'version': '1.0.',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [],
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': self._usdl
            }
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()
        error = False
        try:
            offerings_management.create_offering(user, data)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Invalid version format')

    def test_create_offering_invalid_JSON(self):
        """
        Test the creating of an offering with invalid json document
        """
        data = {
            'na': 'test_offering',
            'version': '1.0',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [],
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': self._usdl
            }
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()
        error = False
        try:
            offerings_management.create_offering(user, data)
        except Exception:
            error = True

        self.assertTrue(error)

    def test_create_offering_invalid_USDL(self):
        """
        Test the creating of an offering with an invalid USDL format
        """
        data = {
            'name': 'test_offering',
            'version': '1.0',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [],
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': 'Invalid data'
            }
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()
        error = False
        try:
            offerings_management.create_offering(user, data)
        except:
            error = True

        self.assertTrue(error)

    def test_create_offering_already_existing(self):

        data = {
            'name': 'test_offering_fail',
            'version': '1.0',
            'repository': 'test_repository',
            'image': {
                'name': 'test_image.png',
                'data': self._image,
            },
            'related_images': [],
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': self._usdl
            }
        }
        user = User.objects.get(username='test_user')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        profile.current_organization = org
        profile.organizations.append({
            'organization': org.pk,
            'roles': ['customer', 'provider']
        })
        profile.save()

        error = False
        msg = None

        try:
            offerings_management.create_offering(user, data)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'The offering already exists')


class OfferingUpdateTestCase(TestCase):

    fixtures = ['update.json']
    _usdl = None

    @classmethod
    def setUpClass(cls):
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor

        path = os.path.join(settings.BASEDIR, 'wstore/test/')
        # loads test USDL
        f = open(os.path.join(path, 'test_usdl.rdf'), 'rb')
        cls._usdl = f.read()
        super(OfferingUpdateTestCase, cls).setUpClass()

    def test_basic_offering_update(self):
        data = {
            'offering_description': {
                'content_type': 'application/rdf+xml',
                'data': self._usdl
            }
        }
        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")

        offerings_management.update_offering(offering, data)

        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")
        usdl = offering.offering_description

        parser = USDLParser(json.dumps(usdl), 'application/json')

        usdl_content = parser.parse()

        self.assertEqual(len(usdl_content['services_included']), 1)
        service = usdl_content['services_included'][0]

        self.assertEqual(service['name'], 'Map viewer')
        self.assertEqual(service['vendor'], 'CoNWeT')

        self.assertEqual(usdl_content['pricing']['title'], 'Map viewer free use')
        self.assertEqual(len(usdl_content['pricing']['price_plans']), 1)

        plan = usdl_content['pricing']['price_plans'][0]
        self.assertEqual(plan['title'], 'Free use')

    def test_offering_update_from_url(self):

        data = {
            'description_url':  "http://examplerep/v1/test_usdl"
        }
        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")

        offerings_management.update_offering(offering, data)

        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")
        usdl = offering.offering_description

        parser = USDLParser(json.dumps(usdl), 'application/json')

        usdl_content = parser.parse()

        self.assertEqual(len(usdl_content['services_included']), 1)
        service = usdl_content['services_included'][0]

        self.assertEqual(service['name'], 'Map viewer')
        self.assertEqual(service['vendor'], 'CoNWeT')

        self.assertEqual(usdl_content['pricing']['title'], 'Map viewer free use')
        self.assertEqual(len(usdl_content['pricing']['price_plans']), 1)

        plan = usdl_content['pricing']['price_plans'][0]
        self.assertEqual(plan['title'], 'Free use')

    def test_offering_update_published(self):

        offering = Offering.objects.get(pk="61000aba8e05ac2115f022f9")

        error = False
        msg = None
        try:
            offerings_management.update_offering(offering, {})
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEquals(msg, 'The offering cannot be edited')

    def test_offering_update_invalid_link(self):

        data = {
            'description_url': {
                'content_type': 'application/rdf+xml',
                'link': 'http://examplerep/v1/invalid'
            }
        }
        offering = Offering.objects.get(pk="61000aba8e15ac2115f022f9")

        error = False
        msg = None
        try:
            offerings_management.update_offering(offering, data)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEquals(msg, 'The provided USDL URL is not valid')


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

    def test_basic_publication(self):
        data = {
            'marketplaces': []
        }
        offering = Offering.objects.get(name='test_offering1')
        offerings_management.publish_offering(offering, data)

        offering = Offering.objects.get(name='test_offering1')
        self.assertEqual(offering.state, 'published')

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

    fixtures = ['bind.json']

    @classmethod
    def setUpClass(cls):
        settings.OILAUTH = False

    def test_basic_binding(self):
        data = [{
            'name': 'test_resource1',
            'version': '1.0'
        }]
        offering = Offering.objects.get(name='test_offering1')
        provider = User.objects.get(username='test_user')
        org = Organization.objects.get(name=provider.username)
        resource = Resource.objects.get(name='test_resource1')
        resource.provider = org
        resource.save()

        offerings_management.bind_resources(offering, data, provider)
        offering = Offering.objects.get(name='test_offering1')

        self.assertEqual(len(offering.resources), 1)
        resource = Resource.objects.get(pk=offering.resources[0])
        self.assertEqual(resource.name, 'test_resource1')
        self.assertEqual(resource.version, '1.0')

    def test_bind_mix_resources(self):
        data = [{
            'name': 'test_resource1',
            'version': '1.0'
        },
        {
            'name': 'test_resource3',
            'version': '1.0'
        }]
        offering = Offering.objects.get(name='test_offering2')
        provider = User.objects.get(username='test_user')

        org = Organization.objects.get(name=provider.username)
        resource = Resource.objects.get(name='test_resource1')
        resource.provider = org
        resource.save()

        resource = Resource.objects.get(name='test_resource3')
        resource.provider = org
        resource.save()

        offerings_management.bind_resources(offering, data, provider)
        offering = Offering.objects.get(name='test_offering2')

        self.assertEqual(len(offering.resources), 2)
        resource = Resource.objects.get(pk=offering.resources[0])
        self.assertEqual(resource.name, 'test_resource1')
        self.assertEqual(resource.version, '1.0')
        resource = Resource.objects.get(pk=offering.resources[1])
        self.assertEqual(resource.name, 'test_resource3')
        self.assertEqual(resource.version, '1.0')
        resource = Resource.objects.get(name='test_resource2')
        self.assertEqual(len(resource.offerings), 0)

    def test_unbind_resources(self):
        data = []

        offering = Offering.objects.get(name='test_offering2')
        provider = User.objects.get(username='test_user')
        offerings_management.bind_resources(offering, data, provider)
        offering = Offering.objects.get(name='test_offering2')

        self.assertEqual(len(offering.resources), 0)

    def test_bind_not_existing_resource(self):
        data = [{
            'name': 'test_resource4',
            'version': '1.0'
        }]
        offering = Offering.objects.get(name='test_offering1')
        provider = User.objects.get(username='test_user')
        error = False
        try:
            offerings_management.bind_resources(offering, data, provider)
        except:
            error = True

        self.assertTrue(error)


class OfferingDeletionTestCase(TestCase):

    tags = ('fiware-ut-5',)
    fixtures = ['del.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.MarketAdaptor = FakeMarketAdaptor
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor
        super(OfferingDeletionTestCase, cls).setUpClass()

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

    def test_delete_published_offering_marketplace(self):
        offering = Offering.objects.get(name='test_offering3')
        offerings_management.delete_offering(offering)
        offering = Offering.objects.get(name='test_offering3')
        self.assertEqual(offering.state, 'deleted')
