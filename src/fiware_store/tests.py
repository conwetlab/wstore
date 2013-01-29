import pymongo
import os
import base64

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from fiware_store.offerings import offerings_management
from fiware_store.models import UserProfile
from fiware_store.models import Offering
from fiware_store.models import Marketplace
from fiware_store.models import Resource


class FakeRepositoryAdaptor():

    _url = None
    _collection = None

    def __init__(self, url, collection):
        self._url = url
        self._collection = collection

    def upload(self, name, cont, data):
        return self._url + self._collection + '/' + name

    def delete(self, ser):
        pass


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
        return {}


class OfferingCreationTestCase(TestCase):

    _db = None
    _image = None
    _usdl = None
    _dir = False
    fixtures = ['create.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        connection = pymongo.MongoClient()
        cls._db = connection.test_database

        # Capture repository calls
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor
        # loads test image
        path = os.path.join(settings.BASEDIR, 'fiware_store/test/')
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
        if self._dir:
            # Remove media files
            dir_name = 'test_organization__test_offering__1.0'
            path = os.path.join(settings.MEDIA_ROOT, dir_name)
            files = os.listdir(path)

            for f in files:
                file_path = os.path.join(path, f)
                os.remove(file_path)

            os.rmdir(path)

        # Remove offering collection
        self._db.fiware_store_offering.drop()
        self._dir = False

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
        profile.organization = 'test_organization'
        profile.save()

        offerings_management.create_offering(user, profile, data)
        self._dir = True
        content = self._db.fiware_store_offering.find_one()

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

        path = os.path.join(settings.BASEDIR, 'fiware_store/test/')
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
        profile.organization = 'test_organization'
        profile.save()

        offerings_management.create_offering(user, profile, data)
        self._dir = True
        content = self._db.fiware_store_offering.find_one()

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
        profile.organization = 'test_organization'
        profile.save()
        try:
            offerings_management.create_offering(user, profile, data)
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
        profile.organization = 'test_organization'
        profile.save()
        try:
            offerings_management.create_offering(user, profile, data)
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
        profile.organization = 'test_organization'
        profile.save()
        try:
            offerings_management.create_offering(user, profile, data)
        except:
            error = True
            self._dir = True

        self.assertTrue(error)


class OfferingRetrievingTestCase(TestCase):

    fixtures = ['get.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.USDLParser = FakeUsdlParser
        super(OfferingRetrievingTestCase, cls).setUpClass()

    def test_get_all_provider_offerings(self):
        #import ipdb;ipdb.set_trace()
        user = User.objects.get(username='test_user')
        offerings = offerings_management.get_provider_offerings(user, 'all')
        self.assertEqual(len(offerings), 3)

        # Check published offering
        self.assertEqual(offerings[2]['name'], 'test_offering3')
        self.assertEqual(offerings[2]['version'], '1.0')
        self.assertEqual(offerings[2]['state'], 'published')
        self.assertEqual(offerings[2]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[2]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[2]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering3__1.0')

        self.assertEqual(len(offerings[2]['resources']), 1)
        resource = offerings[2]['resources'][0]

        self.assertEqual(resource['name'], 'test_resource')
        self.assertEqual(resource['description'], 'Example resource')

    def test_get_provider_uploaded_offerings(self):
        user = User.objects.get(username='test_user')
        offerings = offerings_management.get_provider_offerings(user, 'uploaded')
        self.assertEqual(len(offerings), 2)

        self.assertEqual(offerings[0]['name'], 'test_offering1')
        self.assertEqual(offerings[0]['version'], '1.0')
        self.assertEqual(offerings[0]['state'], 'uploaded')
        self.assertEqual(offerings[0]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[0]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[0]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering1__1.0')

        self.assertEqual(offerings[1]['name'], 'test_offering2')
        self.assertEqual(offerings[1]['version'], '1.1')
        self.assertEqual(offerings[1]['state'], 'uploaded')
        self.assertEqual(offerings[1]['owner_organization'], 'test_organization')
        self.assertEqual(offerings[1]['owner_admin_user_id'], 'test_user')
        self.assertEqual(offerings[1]['description_url'], 'http://testrepository/storeOfferingsCollection/test_organization__test_offering2__1.1')


class OfferingPublicationTestCase(TestCase):

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
        try:
            offerings_management.publish_offering(offering, data)
        except:
            error = True

        self.assertTrue(error)

    def test_publish_offering_no_resources(self):
        data = {
            'marketplaces': ['test_market']
        }
        offering = Offering.objects.get(name='test_offering2')
        try:
            offerings_management.publish_offering(offering, data)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'It is not possible to publish an offering without resources')


class OfferingBindingTestCase(TestCase):

    fixtures = ['bind.json']

    def test_basic_binding(self):
        data = [{
            'name': 'test_resource1',
            'version': '1.0'
        }]
        offering = Offering.objects.get(name='test_offering1')
        provider = User.objects.get(username='test_user')
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
        try:
            offerings_management.bind_resources(offering, data, provider)
        except:
            error = True

        self.assertTrue(error)


class OfferingDeletionTestCase(TestCase):

    fixtures = ['del.json']

    @classmethod
    def setUpClass(cls):
        # Create database connection and load initial data
        offerings_management.MarketAdaptor = FakeMarketAdaptor
        offerings_management.RepositoryAdaptor = FakeRepositoryAdaptor
        super(OfferingDeletionTestCase, cls).setUpClass()

    def test_delete_uploaded_offering(self):
        offering = Offering.objects.get(name='test_offering')
        offerings_management.delete_offering(offering)
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
