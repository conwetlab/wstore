# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

import os
from decimal import Decimal
from datetime import datetime
from mock import MagicMock
from whoosh.fields import Schema, TEXT, KEYWORD, NUMERIC, DATETIME
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from nose_parameterized import parameterized
from whoosh import query
from shutil import rmtree

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.search import search_engine
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


RESULT_ALL = ['test_offering4', 'test_offering5', 'test_offering6', 'test_offering7', 'test_offering8']
RESULT_PURCHASED = ['test_offering2', 'test_offering1']
RESULT_UPLOADED = ['test_offering6']
RESULT_DELETED = ['test_offering7']
RESULT_PUBLISHED = ['test_offering1', 'test_offering2', 'test_offering3', 'test_offering4']
RESULT_COUNT = {
    'number': 4
}

QUERY_PUB = (query.Term('id', '61000aba8e05ac2115155555') & query.Term('state', 'published'))
QUERY_DEL = (query.Term('id', '61000aba8e05ac2115144444') & query.Term('state', 'deleted'))
QUERY_RATED = (query.Term('id', '61000aba8e05ac2115122222') & query.Term('popularity', Decimal(3)))
QUERY_CONTENT = (query.Term('id', '61000aba8e05ac2115166666') & query.Term('content', 'updated'))
QUERY_PURCH = (query.Term('id', '61000aba8e05ac2115122222'))


def _create_index(user):

    index_path = settings.BASEDIR + '/wstore/test/test_index'
    os.makedirs(index_path)

    schema = Schema(
        id=TEXT(stored=True),
        owner=KEYWORD,
        content=TEXT,
        name=KEYWORD(sortable=True),
        popularity=NUMERIC(int, decimal_places=2, sortable=True, signed=False),
        date=DATETIME(sortable=True),
        state=KEYWORD,
        purchaser=KEYWORD
    )

    index = create_in(index_path, schema)
    index_writer = index.writer()

    # Add documents  to the index
    for o in Offering.objects.all():
        if o.state == 'published':
            date = o.publication_date
        else:
            date = o.creation_date

        # Check if purchased
        p = Purchase.objects.filter(offering=o)

        purchasers_text = ''
        if len(p) > 0:
            purchasers_text = unicode(user.userprofile.current_organization.pk)

        if o.owner_admin_user == user:
            owner_pk = unicode(user.userprofile.current_organization.pk)
        else:
            owner_pk = unicode(o.owner_organization.pk)

        index_writer.add_document(
            id=unicode(o.pk),
            owner=owner_pk,
            content=unicode('an offering'),
            name=unicode(o.name),
            popularity=Decimal(o.rating),
            date=date,
            state=unicode(o.state),
            purchaser=purchasers_text
        )

    index_writer.commit()


def _remove_index(ins, off=None, sa=None):
    path = settings.BASEDIR + '/wstore/test/test_index'
    rmtree(path)


def _mock_generator(self):
    search_engine.USDLGenerator = MagicMock()
    self._gen_inst = MagicMock()
    f = open(os.path.join(settings.BASEDIR, 'wstore/test/test_usdl.rdf'), 'rb')
    self._gen_inst.generate_offering_usdl.return_value = (f.read(), 'http://usdluri.com/')
    search_engine.USDLGenerator.return_value = self._gen_inst


class IndexCreationTestCase(TestCase):

    tags = ('fiware-ut-6',)
    fixtures = ['create_index.json']

    def setUp(self):
        _mock_generator(self)

    def tearDown(self):
        reload(search_engine)

    @classmethod
    def tearDownClass(cls):
        path = settings.BASEDIR + '/wstore/test/test_index'
        rmtree(path)

    def test_basic_index_creaton(self):

        offering = Offering.objects.get(name='test_offering')
        se = search_engine.SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
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
        from wstore.offerings import offerings_management
        offerings_management.USDLParser = FakeUSDLParser

        super(FullTextSearchTestCase, cls).setUpClass()

    def tearDown(self):
        try:
            _remove_index(self)
        except:
            pass

    def setUp(self):
        # Fill user info
        user = User.objects.get(username='test_user')
        for p in Purchase.objects.all():
            user.userprofile.offerings_purchased.append(p.offering.pk)

        user.userprofile.save()

        # Include user private organization in the offerings
        for o in Offering.objects.filter(owner_admin_user=user):
            o.owner_organization = user.userprofile.current_organization
            o.save()

        if os.path.exists(settings.BASEDIR + '/wstore/test/test_index'):
            _remove_index(self)

        _create_index(user)

    @parameterized.expand([
        ({}, _remove_index, None, False, None, None, Exception, 'The index does not exist'),
        ({}, None, 'invalid', False, None, None, ValueError, 'Invalid state'),
        ({}, None, None, False, None, 'invalid', ValueError, 'Undefined sorting'),
        ({}, None, None, False, (2, 4), None, TypeError, 'Invalid pagination type'),
        ({}, None, None, False, {'start': 1}, None, ValueError, 'Missing required field in pagination'),
        ({}, None, None, False, {'start': 'a1', 'limit': 2}, None, TypeError, 'Invalid pagination params type'),
        ({}, None, None, False, {'start': 0, 'limit': 2}, None, ValueError, 'Start param must be higher than 0'),
        ({}, None, None, False, {'start': 1, 'limit': -2}, None, ValueError, 'Limit param must be positive'),
        (RESULT_ALL, None, ['uploaded', 'published', 'deleted'],),
        (RESULT_PURCHASED, None, ['purchased'], False, None, 'popularity'),
        (RESULT_UPLOADED, None, ['uploaded'], False, {'start': 1, 'limit': 1}, 'date'),
        (RESULT_DELETED, None, ['deleted'], False, {'start': 1, 'limit': 1}, 'name'),
        (RESULT_PUBLISHED, None, None, False, None, 'name'),
        (RESULT_COUNT, None, None, True)
    ])
    def test_search_offerings(self, expected_result, side_effect=None, state=None, count=False, pagination=None, sort=None, err_type=None, err_msg=None):

        # Create user data
        user = User.objects.get(username='test_user')

        if side_effect:
            side_effect(self)

        # Create the search engine
        se = search_engine.SearchEngine(settings.BASEDIR + '/wstore/test/test_index')

        # Call full text search
        error = None
        try:
            result = se.full_text_search(user, 'offering', state=state, count=count, pagination=pagination, sort=sort)
        except Exception as e:
            error = e

        # Check results
        if not err_type:
            self.assertEquals(error, None)
            if count:
                self.assertEquals(result, expected_result)
            else:
                # If a sorting has been defined the result must be strict
                self.assertEquals(len(result), len(expected_result))

                i = 0
                for res in result:
                    if sort:
                        self.assertEquals(res['name'], expected_result[i])
                    else:
                        self.assertTrue(res['name'] in expected_result)
                    i += 1
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


class UpdateIndexTestCase(TestCase):

    tags = ('fiware-ut-6',)
    fixtures = ['update_index.json']

    @classmethod
    def setUpClass(cls):
        from wstore.offerings import offerings_management
        offerings_management.USDLParser = FakeUSDLParser
        cls.date = datetime.now()

        super(UpdateIndexTestCase, cls).setUpClass()

    def tearDown(self):
        try:
            _remove_index(self)
        except:
            pass
        reload(search_engine)

    def setUp(self):
        # Fill user info
        _mock_generator(self)
        user = User.objects.get(username='test_user')
        for p in Purchase.objects.all():
            user.userprofile.offerings_purchased.append(p.offering.pk)

        user.userprofile.save()

        # Include user private organization in the offerings
        for o in Offering.objects.filter(owner_admin_user=user):
            o.owner_organization = user.userprofile.current_organization
            o.save()

        if os.path.exists(settings.BASEDIR + '/wstore/test/test_index'):
            _remove_index(self)

        _create_index(user)

    def _update_published(self, offering, sa=None):
        offering.state = "published"
        offering.publication_date = self.date
        offering.save()

    def _update_deleted(self, offering, sa=None):
        offering.state = "deleted"
        offering.save()

    def _update_rated(self, offering, sa=None):
        offering.rating = 3.0
        offering.save()

    def _update_content(self, offering, sa=None):
        sa._aggregate_text = MagicMock()
        sa._aggregate_text.return_value = "updated"

    def _update_purchased(self, offering, sa=None):
        user = User.objects.get(pk="51000aba8e05ac2115f022f9")

        Purchase.objects.create(
            customer=user,
            date=self.date,
            offering=offering,
            organization_owned=False,
            state='pending',
            tax_address={},
            owner_organization=user.userprofile.current_organization
        )

    @parameterized.expand([
        (_update_published, '61000aba8e05ac2115155555', QUERY_PUB),
        (_update_deleted, '61000aba8e05ac2115144444', QUERY_DEL),
        (_update_rated, '61000aba8e05ac2115111111', QUERY_RATED),
        (_update_content, '61000aba8e05ac2115166666', QUERY_CONTENT),
        (_update_purchased, '61000aba8e05ac2115122222', QUERY_PURCH, True),
        (_remove_index, '', None, False, Exception, 'The index does not exist')
    ])
    def test_update_index(self, update_method, offering, query_, owned=False, err_type=None, err_msg=None):

        # Get the offering
        off = None
        if not err_type:
            off = Offering.objects.get(pk=offering)

        # Create the search engine
        se = search_engine.SearchEngine(settings.BASEDIR + '/wstore/test/test_index')

        # Call the update method
        update_method(self, off, sa=se)

        # Call full text search
        error = None
        try:
            se.update_index(off)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            index = open_dir(settings.BASEDIR + '/wstore/test/test_index')

            with index.searcher() as searcher:
                if owned:
                    user = User.objects.get(pk="51000aba8e05ac2115f022f9")
                    pk = user.userprofile.current_organization.pk
                    query_ = query_ & query.Term('purchaser', pk)

                search_result = searcher.search(query_)

                self.assertEquals(len(search_result), 1)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)
