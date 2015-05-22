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
import json
import types
import shutil
from decimal import Decimal
from mock import MagicMock
from nose_parameterized import parameterized
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from stemming.porter2 import stem

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from wstore.social.tagging import recommendation_manager, tag_manager, views
from wstore.models import Organization, Offering


class TagCooccurrenceTestCase(TestCase):

    tags = ('tagging', 'fiware-ut-30')

    def tearDown(self):
        reload(recommendation_manager)
        TestCase.tearDown(self)

    def _search_mock(self, tag):
        search_result = {
            'test': [{
                'id': '1111111111',
                'tags': 'thing mock test user',
                'named_tags': 'thing mock test user'
            }, {
                'id': '2222222222',
                'tags': 'test mock reference use',
                'named_tags': 'test mock reference use'
            }],
            'widget': [{
                'id': '333333333',
                'tags': 'widget wirecloud mashup platform',
                'named_tags': 'widget wirecloud mashup platform'
            }, {
                'id': '444444444',
                'tags': 'widget wirecloud',
                'named_tags': 'widget wirecloud'
            }],
            'servic': [{
                'id': '5555555555',
                'tags': 'servic soa architecture',
                'named_tags': 'service soa architecture'
            }, {
                'id': '6666666666',
                'tags': 'servic user',
                'named_tags': 'service user'
            }],
            'notag': []
            }
        return search_result[tag]

    @parameterized.expand([
        ({'test'}, ('thing', 'mock', 'user', 'reference', 'use'), ('0.5', '1', '0.5', '0.5', '0.5')),
        ({'widget'}, ('wirecloud', 'mashup', 'platform'), ('1', '0.5', '0.5')),
        ({'service'}, ('soa', 'architecture', 'user'), ('0.5', '0.5', '0.5')),
        ({'notag'}, (), ()),
        ({'test', 'widget', 'service', 'notag'}, ('thing', 'mock', 'reference', 'use', 'wirecloud', 'mashup', 'platform', 'soa', 'architecture', 'user'), 
         ('0.17', '0.33', '0.17', '0.17', '0.33', '0.17', '0.17', '0.17','0.17', '0.33')),
        ({'service'}, ('service', 'soa', 'architecture', 'user'), ('1', '0.5', '0.5', '0.5'), True)
    ])
    def test_tagging_coocurrence(self, user_tags, tags, scores, use_tags=False):
        # Create mocks
        recommendation_manager.TagManager = MagicMock
        recommendation_manager.TagManager.get_index_doc_by_tag = self._search_mock

        result_list = []
        # Call class
        co_class = recommendation_manager.CooccurrenceThead(result_list, user_tags, include_user_tags=use_tags)
        co_class.run()

        # Check results
        self.assertEquals(len(result_list), len(tags))
        for t in result_list:
            ix = tags.index(t[1])
            self.assertEquals(str(t[2]), scores[ix])


class USDLTagsTestCase(TestCase):

    tags = ('tagging', 'fiware-ut-30')

    def tearDown(self):
        reload(recommendation_manager)
        TestCase.tearDown(self)

    def _aggregate_mock(self, offering):
        return "CoNWeT   Terms and conditions Description of the terms and conditions applied to this widget Android 2011-12-01 2011-12-31  Map viewer free use   Map viewer description"

    def test_usdl_tagging_recommendation(self):
        # Create mocks
        recommendation_manager.SearchEngine = MagicMock
        recommendation_manager.SearchEngine._aggregate_text = self._aggregate_mock

        # Call class
        co_class = recommendation_manager.USDLEntitiesRetrieving(None)
        result_list = co_class.get_named_entities()

        expected_result = ['conwet', 'term', 'condit', 'descript', 'appli', 'widget', 'android', '2011',
            '12','01', '31','map','viewer','free', 'us']

        self.assertEquals(len(result_list), len(expected_result))
        for res in result_list:
            self.assertTrue(res in expected_result)


class TagManagementTestCase(TestCase):

    tags = ('tagging', 'fiware-ut-30')
    _path = None

    @classmethod
    def setUpClass(cls):
        from os import path
        from django.conf import settings
        cls._path = path.join(settings.BASEDIR, 'wstore')
        cls._path = path.join(cls._path, 'test')
        cls._path = path.join(cls._path, 'test_index')
        super(TagManagementTestCase, cls).setUpClass()

    def tearDown(self):
        if os.path.exists(self._path):
            shutil.rmtree(self._path)
        reload(tag_manager)

    def _create_index_dir(self):
        # Create indexes
        os.makedirs(self._path)
        # Create schema
        schema = Schema(id=ID(stored=True, unique=True), tags=KEYWORD(stored=True), named_tags=KEYWORD(stored=True))
        # Create index
        index = create_in(self._path, schema)
        index_writer = index.writer()
        index_writer.add_document(id=unicode('11111'), tags=unicode('test1 test2'), named_tags=unicode('test1 test2'))
        index_writer.add_document(id=unicode('22222'), tags=unicode('test1 test3 test4'), named_tags=unicode('test1 test3 test4'))
        index_writer.add_document(id=unicode('33333'), tags=unicode('test2 test5 test6'), named_tags=unicode('test2 test5 test6'))
        index_writer.commit()

    @parameterized.expand([
        (False, '1111111111', ['test1', 'test2']),
        (True, '2222222222', ['test3', 'test4'])
    ])
    def test_update_tags(self, create_dir, pk, tags):
        if create_dir:
            os.makedirs(self._path)
            # Create schema
            schema = Schema(id=ID(stored=True, unique=True), tags=KEYWORD(stored=True), named_tags=KEYWORD(stored=True))
            # Create index
            index = create_in(self._path, schema)
            index_writer = index.writer()
            index_writer.add_document(id=unicode(pk), tags=unicode('test1 test2'), named_tags=unicode('test1 test2'))
            index_writer.commit()

        offering = MagicMock()
        offering.pk = pk
        offering.save = MagicMock()

        tag_man = tag_manager.TagManager(index_path=self._path)
        tag_man.update_tags(offering, tags)

        self.assertEquals(offering.tags, tags)

        # Query the index
        index = open_dir(self._path)
        with index.searcher() as searcher:
            query = QueryParser('id', index.schema).parse(unicode(pk))
            val = searcher.search(query)
            self.assertEquals(len(val), 1)
            self.assertEquals(val[0]['id'], unicode(pk))
            ret_tags = val[0]['tags'].split(' ')
            self.assertEquals(len(tags), len(ret_tags))

            for t in tags:
                self.assertTrue(t in ret_tags)

    def test_search_by_tag(self):
        # Create mock offerings
        tag_manager.Offering = MagicMock()

        def get_mock(pk=None):
            id_field = {
                '11111': 'offering1',
                '22222': 'offering2',
                '33333': 'offering3'
            }
            return id_field[pk]

        self._create_index_dir()
        tag_manager.Offering.objects.get = get_mock

        tm = tag_manager.TagManager(self._path)
        offerings = tm.search_by_tag('test1')

        self.assertEquals(len(offerings), 2)
        self.assertTrue('offering1' in offerings)
        self.assertTrue('offering2' in offerings)

    @parameterized.expand([
        ('', '11111'),
        ('not_indexes', '11111','Indexes has not been created', 'wstore/test/ix'),
        ('not_offering', '44444','No tag indexes has been created for the given offering')
    ])
    def test_delete_tag_document(self, name, pk, err_msg=None, ix_path=None):
        # Create mock
        offering = MagicMock()
        offering.pk = pk

        # Create indexes
        self._create_index_dir()

        path = self._path
        if ix_path:
            from django.conf import settings
            path = os.path.join(settings.BASEDIR, ix_path)

        # Build the tag manager
        tm = tag_manager.TagManager(path)

        error = None
        try:
            tm.delete_tag(offering)
        except Exception as e:
            error = e

        # Check response
        if not err_msg:
            self.assertEquals(error, None)
            # Check that the index does not exists
            index = open_dir(self._path)
            with index.searcher() as searcher:
                query = QueryParser('id', index.schema).parse(unicode(offering.pk))
                self.assertEquals(len(searcher.search(query)), 0)
        else:
            self.assertTrue(isinstance(error, ValueError))
            self.assertEquals(unicode(error), err_msg)

class TagViewTestCase(TestCase):

    tags = ('tagging', 'fiware-ut-30')
    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create(
            username='test_user',
            email='a@b.com',
            first_name='test',
            last_name='user'
        )
        self.user.set_password('passwd')

    def tearDown(self):
        reload(views)
        TestCase.tearDown(self)

    def _get_offering(self, owner_organization=None, name=None, version=None):
        if name!= 'test_offering':
            raise Exception('')

        off_object = MagicMock()
        off_object.tags = ['tag3', 'tag4']

        return off_object

    @parameterized.expand([
        ({'organization': 'test_org', 'name': 'test_offering', 'version': '1.0'},'recommend', False, ['tag1', 'tag2'], 200),
        ({'organization': 'test_org', 'name': 'test_offering', 'version': '1.0'}, None, False, ['tag3', 'tag4'], 200),
        ({'organization': 'test_org', 'name': 'not_found', 'version': '1.0'}, None, True, 'Not found', 404),
        ({'organization': 'test_org', 'name': 'test_offering', 'version': '1.0'}, 'invalid', True, 'Invalid action', 400)
    ])
    def test_tag_retrieving(self, off_data, action, error, response_content, code):
        # Create mocks
        org = MagicMock()
        org.objects.get = MagicMock()
        org.objects.get.return_value = MagicMock()
        offering = MagicMock()
        offering.objects.get = self._get_offering

        rec_manager = MagicMock()
        rec_manager_instance = MagicMock()
        rec_manager_instance.get_recommended_tags = MagicMock()
        rec_manager_instance.get_recommended_tags.return_value = [('tag1', '0.5'),('tag2', '0.5')]
        rec_manager.return_value = rec_manager_instance

        views.Organization = org
        views.Offering = offering
        views.RecommendationManager = rec_manager

        # Create the view
        tag_collection = views.TagCollection(permitted_methods=('GET', 'PUT'))
        url = '/api/offering/offerings/' + off_data['organization'] +'/' + off_data['name'] + '/' + off_data['version'] +'/tags'

        if action:
            url += '?action=' + action

        request = self.factory.get(url,HTTP_ACCEPT='application/json; charset=utf-8')
        request.user = self.user

        # Get HTTP response
        response = tag_collection.read(request, off_data['organization'], off_data['name'], off_data['version'])

        parsed_response = json.loads(response.content)

        # Check response
        self.assertEqual(response.status_code, code)
        if not error:
            self.assertEquals(len(parsed_response['tags']), len(response_content))
            for tag in response_content:
                self.assertTrue(tag in parsed_response['tags'])
        else:
            self.assertEqual(parsed_response['message'], response_content)
            self.assertEqual(parsed_response['result'], 'error')

    @parameterized.expand([
        ({'organization': 'test_org', 'name': 'test_offering', 'version': '1.0'}, 'correct', 'OK', 200),
        ({'organization': 'test_org', 'name': 'test_offering', 'version': '1.0'}, 'error', 'Forbidden', 403),
        ({'organization': 'test_org', 'name': 'not_found', 'version': '1.0'}, 'error', 'Not found', 404),
        ({'organization': 'test_org', 'name': 'test_offering', 'version': '1.0'}, 'error', 'Exception', 400)
    ])
    def test_tag_update(self, off_data, result, response_content, code):
        # Create mocks
        org = Organization.objects.create(name='test_org')
        offering = MagicMock()
        offering.objects.get = self._get_offering

        tag_manager = MagicMock()
        tag_manager_instance = MagicMock()
        tag_manager_instance.update_tags = MagicMock()

        if code != 403:
            self.user.userprofile.current_organization = org
            self.user.userprofile.save()
        if code == 400:
            tag_manager_instance.update_tags.side_effect = Exception(response_content)

        tag_manager.return_value = tag_manager_instance

        views.Offering = offering
        views.Organization = Organization
        views.TagManager = tag_manager

        # Create the view
        tag_collection = views.TagCollection(permitted_methods=('GET', 'PUT'))
        url = '/api/offering/offerings/' + off_data['organization'] +'/' + off_data['name'] + '/' + off_data['version'] +'/tags'

        data = {'tags': ['tag1', 'tag2']}
        request = self.factory.put(
            url,
            json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        request.user = self.user

        response = tag_collection.update(request, off_data['organization'], off_data['name'], off_data['version'])
        parsed_response = json.loads(response.content)

        # Check response
        self.assertEqual(response.status_code, code)
        self.assertEqual(parsed_response['message'], response_content)
        self.assertEqual(parsed_response['result'], result)


class RecommendationProcessTestCase(TestCase):

    tags = ('tagging', 'fiware-ut-30')
    fixtures = ('tagging.json',)
    _init_copy = None

    @classmethod
    def setUpClass(cls):
        from os import path
        from django.conf import settings
        cls._path = path.join(settings.BASEDIR, 'wstore')
        cls._path = path.join(cls._path, 'test')
        cls._path = path.join(cls._path, 'test_index2')
        super(RecommendationProcessTestCase, cls).setUpClass()

    def tearDown(self):
        if os.path.exists(self._path):
            for f in os.listdir(self._path):
                file_path = os.path.join(self._path, f)
                os.remove(file_path)
            os.rmdir(self._path)
        # Restore Tag init
        if self._init_copy:
            recommendation_manager.TagManager.__init__ = self._init_copy

        reload(recommendation_manager)

    def test_tag_aggregation(self):
        # Create tag recommendation manager
        recom_manager = recommendation_manager.RecommendationManager(MagicMock(), ['test1', 'test2', 'test3'])
        # Load tag lists
        recom_manager._coocurrence_tags = [
            ('test1', 'test1', Decimal('0.5')),
            ('servic', 'service', Decimal('0.17')),
            ('widget', 'widget', Decimal('0.23')),
            ('us', 'use', Decimal('0.10'))
        ]
        recom_manager._usdl_coocurrence_tags = [
            ('servic', 'service', Decimal('0.20')),
            ('thing', 'thing', Decimal('0.15'))
        ]
        # Check returned list
        aggregated_list = recom_manager._aggregate_tags()

        self.assertEquals(len(aggregated_list), 4)
        expected_result = {
            'service': Decimal('0.20'),
            'widget': Decimal('0.23'),
            'use': Decimal('0.10'),
            'thing': Decimal('0.15')
        }

        for tag, rank in aggregated_list:
            self.assertEquals(expected_result[tag], rank)

    def test_complete_recommendation_process(self):
        # Test the complete recommendation process

        # Create indexes
        os.makedirs(self._path)
        # Create schema
        schema = Schema(id=ID(stored=True, unique=True), tags=KEYWORD(stored=True), named_tags=KEYWORD(stored=True))
        # Create index
        index = create_in(self._path, schema)
        index_writer = index.writer()
        for off in Offering.objects.all():
            # Create stemmed tags text
            # Create tags text
            text = ''
            named_text = ''
            # Create tags text
            for tag in off.tags:
                text += stem(tag) + ' '
                named_text += tag + ' '

            if text:
                index_writer.add_document(id=unicode(off.pk), tags=text, named_tags=named_text)

        index_writer.commit()

        # Override TagManager init method in order to avoid default index path
        def new_init(tag_self, path=None):
            tag_self._index_path = self._path

        old_init = recommendation_manager.TagManager.__init__
        self._init_copy = types.FunctionType(old_init.func_code, old_init.func_globals, name = old_init.func_name,
                       argdefs = old_init.func_defaults,
                       closure = old_init.func_closure)

        recommendation_manager.TagManager.__init__ = new_init

        # Create recommendation offering
        main_offering = Offering.objects.get(pk="51100aba8e05ac2115f022f0")

        # Launch recommendation process
        recom_manager = recommendation_manager.RecommendationManager(main_offering, set(['fiware', 'youtube']))

        recommendations = recom_manager.get_recommended_tags()

        # Check recommendation list
        self.assertEquals(len(recommendations), 9)

        expected_result = {
            'cloud': Decimal('0.5'),
            'portal': Decimal('0.5'),
            'free': Decimal('1'),
            'multimedia': Decimal('0.5'),
            'flickr': Decimal('0.5'),
            'wikipedia': Decimal('0.5'),
            'widget': Decimal('1'),
            'wirecloud': Decimal('1'),
            'map': Decimal('1')
        }

        for res in recommendations:
            self.assertEquals(res[1], expected_result[res[0]])
