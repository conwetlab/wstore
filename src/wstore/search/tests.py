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

import os
from decimal import Decimal
from whoosh.fields import Schema, TEXT, KEYWORD, NUMERIC, DATETIME
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from nose_parameterized import parameterized

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.search.search_engine import SearchEngine
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
    'count': 4
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

def _remove_index(ins):
    path = settings.BASEDIR + '/wstore/test/test_index'
    files = os.listdir(path)
    for f in files:
        file_path = os.path.join(path, f)
        os.remove(file_path)

    os.rmdir(path)


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
        ({}, None, None, False, (2,4), None, TypeError, 'Invalid pagination type'),
        ({}, None, None, False, {'start': 1}, None, ValueError, 'Missing required field in pagination'),
        ({}, None, None, False, {'start': 'a1', 'limit': 2}, None, TypeError, 'Invalid pagination params type'),
        ({}, None, None, False, {'start': 0, 'limit': 2}, None, ValueError, 'Start param must be higher than 0'),
        ({}, None, None, False, {'start': 1, 'limit': -2}, None, ValueError, 'Limit param must be positive'),
        (RESULT_ALL, None, 'all',),
        (RESULT_PURCHASED, None, 'purchased', False, None, 'popularity'),
        (RESULT_UPLOADED, None, 'uploaded', False, {'start': 1, 'limit': 1}, 'date'),
        (RESULT_DELETED, None, 'deleted', False, {'start': 1, 'limit': 1}),
        (RESULT_PUBLISHED, None, None, False, None, 'name'),
        (RESULT_COUNT, None, None, True)
    ])
    def test_search_offerings(self, expected_result, side_effect=None, state=None, count=False, pagination=None, sort=None, err_type=None, err_msg=None):

        # Create user data
        user = User.objects.get(username='test_user')

        if side_effect:
            side_effect(self)

        # Create the search engine
        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')

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
