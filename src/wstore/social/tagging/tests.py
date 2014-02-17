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
from mock import MagicMock
from nose_parameterized import parameterized
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

from django.test import TestCase

from wstore.social.tagging import recommendation_manager, tag_manager


class TagCooccurrenceTestCase(TestCase):

    tags = ('tagging',)

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

    tags = ('tagging', )

    def _aggregate_mock(self, offering):
        return "CoNWeT   Terms and conditions Description of the terms and conditions applied to this widget Android 2011-12-01 2011-12-31  Map viewer free use   Map viewer description"
    
    def test_usdl_tagging_recomendation(self):
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

    tags = ('tagging',)
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
            for f in os.listdir(self._path):
                file_path = os.path.join(self._path, f)
                os.remove(file_path)
            os.rmdir(self._path)

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

        tag_manager.Offering.objects.get = get_mock

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

        tm = tag_manager.TagManager(self._path)
        offerings = tm.search_by_tag('test1')

        self.assertEquals(len(offerings), 2)
        self.assertTrue('offering1' in offerings)
        self.assertTrue('offering2' in offerings)
