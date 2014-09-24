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

from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase
from django.conf import settings
from django.core.management import call_command

from wstore.management.commands import configureproject, createindexes, createtags


class ConfigureProjectTestCase(TestCase):
    tags = ('management', )

    def setUp(self):
        # Mock stdin
        configureproject.stdin = MagicMock()
        TestCase.setUp(self)

    def tearDown(self):
        reload(configureproject)
        TestCase.tearDown(self)

    @parameterized.expand([
        ('basic', )
    ])
    def test_configure_proyect(self, name):
        pass


class IndexTestCase(TestCase):

    def setUp(self):
        # Mock the standard input
        self.tested_mod.stdin = MagicMock()
        self.tested_mod.stdin.readline.return_value = 'y '
        # Mock rmtree
        self.tested_mod.rmtree = MagicMock()
        TestCase.setUp(self)

    def _invalid_option(self):
        def mock_rl():
            self.tested_mod.stdin.readline = MagicMock()
            self.tested_mod.stdin.readline.return_value = 'y '
            return 't '

        self.tested_mod.stdin.readline = mock_rl

    def _canceled(self):
        self.tested_mod.stdin.readline.return_value = 'n '

    def manager_assertion(self):
        pass

    def _index_tst(self, info, input_=True, side_effect=None, completed=True):

        args = []
        opts = {}
        if not input_:
            args.append('--no-input')

        if side_effect:
            side_effect(self)

        call_command(info['command'], *args, **opts)

        if completed:
            index_path = os.path.join(settings.BASEDIR, 'wstore')
            index_path = os.path.join(index_path, info['module'])
            index_path = os.path.join(index_path, 'indexes')

            # Check calls
            self.tested_mod.rmtree.assert_called_once_with(index_path, True)

            self.manager_assertion()
        else:
            called = True
            try:
                self.tested_mod.rmtree.assert_any_call()
            except:
                called = False

            self.assertFalse(called)


class CreateIndexesTestCase(IndexTestCase):
    tags = ('management',)

    def __init__(self, methodName='runTest'):
        self.tested_mod = createindexes
        IndexTestCase.__init__(self, methodName=methodName)

    def setUp(self):
        # Mock search engine
        self.se_inst = MagicMock()
        createindexes.SearchEngine = MagicMock()
        createindexes.SearchEngine.return_value = self.se_inst
        # Mock offerings
        self.tested_mod.Offering = MagicMock()
        self.offerings = [
            'offering1',
            'offering2',
            'offering3'
        ]
        self.tested_mod.Offering.objects.all.return_value = self.offerings
        IndexTestCase.setUp(self)

    def tearDown(self):
        reload(createindexes)
        IndexTestCase.tearDown(self)

    def manager_assertion(self):
        self.se_inst.create_index.assert_calls(self.offerings, True)
        IndexTestCase.manager_assertion(self)

    @parameterized.expand([
        ('no_input', False),
        ('interactive',),
        ('inter_inv', True, IndexTestCase._invalid_option),
        ('canceled', True, IndexTestCase._canceled, False)
    ])
    def test_create_indexes(self, name, input_=True, side_effect=None, completed=True):

        info = {
            'command': 'createindexes',
            'module': 'search'
        }
        self._index_tst(info, input_=input_, side_effect=side_effect, completed=completed)


class CreateTagIndexesTestCase(IndexTestCase):

    tags = ('management',)

    def __init__(self, methodName='runTest'):
        self.tested_mod = createtags
        IndexTestCase.__init__(self, methodName=methodName)

    def setUp(self):
        # Mock Tagging manager
        self.tm_inst = MagicMock()
        createtags.TagManager = MagicMock()
        createtags.TagManager.return_value = self.tm_inst
        # Mock offerings
        self.offering = MagicMock()
        self.offering.tags = ['tag1']
        createtags.Offering = MagicMock()
        createtags.Offering.objects.all.return_value = [
            self.offering
        ]
        IndexTestCase.setUp(self)

    def tearDown(self):
        reload(createtags)
        IndexTestCase.tearDown(self)

    def manager_assertion(self):
        self.tm_inst.update_tags.assert_called_once_with(self.offering, ['tag1'])
        IndexTestCase.manager_assertion(self)

    @parameterized.expand([
        ('no_input', False),
        ('interactive',),
        ('inter_inv', True, IndexTestCase._invalid_option),
        ('canceled', True, IndexTestCase._canceled, False)
    ])
    def test_create_tag_indexes(self, name, input_=True, side_effect=None, completed=True):

        info = {
            'command': 'createtags',
            'module': 'social'
        }
        self._index_tst(info, input_=input_, side_effect=side_effect, completed=completed)
