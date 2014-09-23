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

from wstore.management.commands import configureproject, createindexes


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


class CreateIndexesTestCase(TestCase):

    tags = ('management',)

    def setUp(self):
        # Mock search engine
        self.se_inst = MagicMock()
        createindexes.SearchEngine = MagicMock()
        createindexes.SearchEngine.return_value = self.se_inst
        # Mock the standard input
        createindexes.stdin = MagicMock()
        createindexes.stdin.readline.return_value = 'y '
        # Mock rmtree
        createindexes.rmtree = MagicMock()
        # Mock offerings
        createindexes.Offering = MagicMock()
        self.offerings = [
            'offering1',
            'offering2',
            'offering3'
        ]
        createindexes.Offering.objects.all.return_value = self.offerings
        TestCase.setUp(self)

    def tearDown(self):
        reload(createindexes)
        TestCase.tearDown(self)

    def _invalid_option(self):
        def mock_rl():
            createindexes.stdin.readline = MagicMock()
            createindexes.stdin.readline.return_value = 'y '
            return 't '

        createindexes.stdin.readline = mock_rl

    def _canceled(self):
        createindexes.stdin.readline.return_value = 'n '

    @parameterized.expand([
        ('no_input', False),
        ('interactive',),
        ('inter_inv', True, _invalid_option),
        ('canceled', True, _canceled, False)
    ])
    def test_create_indexes(self, name, input_=True, side_effect=None, completed=True):

        args = []
        opts = {}
        if not input_:
            args.append('--no-input')

        call_command('createindexes', *args, **opts)

        if completed:
            index_path = os.path.join(settings.BASEDIR, 'wstore')
            index_path = os.path.join(index_path, 'search')
            index_path = os.path.join(index_path, 'indexes')

            # Check calls
            createindexes.rmtree.assert_called_once_with(index_path, True)

            self.se_inst.create_index.assert_calls(self.offerings, True)
