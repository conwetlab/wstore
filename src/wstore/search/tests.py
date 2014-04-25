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

import os
from whoosh.fields import Schema, TEXT
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.search.search_engine import SearchEngine
from wstore.models import UserProfile
from wstore.models import Organization
from wstore.models import Offering
from wstore.contracting.models import Purchase


__test__ = False


class FakeUSDLParser():

    def __init__(self, data, type_):
        pass

    def parse(self):
        return {
            'pricing': {
                'price_plans': [{
                    'price_components': []
                }]
            }
        }


class IndexCreationTestCase(TestCase):

    tags = ('fiware-ut-6',)
    fixtures = ['create_index.json']

    @classmethod
    def tearDownClass(cls):
        path = settings.BASEDIR + '/wstore/test/test_index'
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            os.remove(file_path)

        os.rmdir(path)

    def test_basic_index_creaton(self):

        offering = Offering.objects.get(name='test_offering')
        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        se.create_index(offering)

        # Get the index reader
        index = open_dir(settings.BASEDIR + '/wstore/test/test_index')

        with index.searcher() as searcher:
            query = QueryParser('content', index.schema).parse(unicode('widget'))
            total_hits = searcher.search(query)

            self.assertEqual(len(total_hits), 1)
            doc = total_hits[0]
            self.assertEqual(offering.pk, doc['id'])


class FullTextSearchTestCase(TestCase):

    tags = ('fiware-ut-6',)
    fixtures = ['full_text.json']

    @classmethod
    def setUpClass(cls):
        # Create the test index
        index_path = settings.BASEDIR + '/wstore/test/test_index'
        os.makedirs(index_path)
        schema = Schema(id=TEXT(stored=True), content=TEXT)
        index = create_in(index_path, schema)
        index_writer = index.writer()

        # Add documents  to the index

        text1 = 'first test index offering'
        index_writer.add_document(id=unicode("61000aba8e05ac2115f022f9"), content=unicode(text1))

        text2 = 'second test index offering'
        index_writer.add_document(id=unicode("61000aba8e05ac2115f022ff"), content=unicode(text2))

        index_writer.add_document(id=unicode("61000aba8e05ac2115f022f0"), content=unicode("uploaded"))

        index_writer.add_document(id=unicode("61000a0a8905ac2115f022f0"), content=unicode("purchased"))

        index_writer.add_document(id=unicode("6108888a8905ac2115f022f0"), content=unicode("multiple"))

        index_writer.commit()

        from wstore.offerings import offerings_management
        offerings_management.USDLParser = FakeUSDLParser

        super(FullTextSearchTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        path = settings.BASEDIR + '/wstore/test/test_index'
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            os.remove(file_path)

        os.rmdir(path)

    def test_basic_search(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'first')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test_offering1')
        self.assertEqual(result[0]['version'], '1.0')

    def test_search_multiple_results(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'index offering')

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'test_offering1')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[1]['name'], 'test_offering2')
        self.assertEqual(result[1]['version'], '1.0')

    def test_search_no_results(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'no result')

        self.assertEqual(len(result), 0)

    def test_search_for_uploaded_offerings(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'uploaded', state='uploaded')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'uploaded_offering')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[0]['state'], 'uploaded')

    def test_search_for_purchased_offerings(self):

        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.save()
        org.offerings_purchased = ["61000a0a8905ac2115f022f0"]
        org.save()
        purchase = Purchase.objects.all()[0]
        purchase.organization_owned = True
        purchase.owner_organization = org
        purchase.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'purchased', state='purchased')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'purchased_offering')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[0]['state'], 'purchased')

    def test_search_for_purchased_offerings_user(self):

        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.offerings_purchased = ["61000a0a8905ac2115f022f0"]
        user_profile.save()
        org.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'purchased', state='purchased')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'purchased_offering')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[0]['state'], 'purchased')

    def test_search_for_purchased_offerings_multiple(self):

        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization1')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.offerings_purchased = ["61000a0a8905ac2115f022f0"]
        user_profile.save()
        org.offerings_purchased = ["6108888a8905ac2115f022f0"]
        org.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'multiple', state='purchased')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'purchased_offering3')
        self.assertEqual(result[0]['version'], '1.1')
        self.assertEqual(result[0]['state'], 'purchased')

    def test_search_not_existing_index(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.current_organization = org
        user_profile.organizations.append({
            'organization': org.pk,
            'roles': ['provider', 'customer']
        })
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/no_index')

        error = False
        msg = None
        try:
            se.full_text_search(user, 'index offering')
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'The index does not exist')
