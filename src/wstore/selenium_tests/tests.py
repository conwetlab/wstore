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
import shutil
import rdflib

from django.conf import settings
from django.contrib.auth.models import User

from wstore.store_commons.utils.testing import save_indexes, restore_indexes
from wstore.search.search_engine import SearchEngine
from wstore.selenium_tests.testcase import WStoreSeleniumTestCase
from wstore.offerings.offerings_management import _create_basic_usdl
from wstore.models import Offering


def _fill_offering_description(pk, usdl_info):
    offering = Offering.objects.get(pk=pk)

    usdl = _create_basic_usdl(usdl_info)
    graph = rdflib.Graph()
    graph.parse(data=usdl, format='application/rdf+xml')
    offering.offering_description = json.loads(graph.serialize(format='json-ld', auto_compact=True))
    offering.owner_organization = User.objects.get(username="provider").userprofile.current_organization
    offering.save()


def _create_indexes():
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    search_engine = SearchEngine(index_path)

    for off in Offering.objects.all():
        search_engine.create_index(off)


class BasicNavigationTestCase(WStoreSeleniumTestCase):

    tags = ('selenium', )
    _dirs_to_remove = []

    def __init__(self, methodName='runTest'):
        WStoreSeleniumTestCase.__init__(self, methodName=methodName)
        self.fixtures.extend(['basic_offerings.json'])

    def tearDown(self):
        # Remove directories
        for path in self._dirs_to_remove:
            try:
                files = os.listdir(path)
                for f in files:
                    file_path = os.path.join(path, f)
                    os.remove(file_path)

                os.rmdir(path)
            except:
                pass
        restore_indexes()
        WStoreSeleniumTestCase.tearDown(self)

    def _check_search_container(self, offering_names):
        # Check offerings container
        container = self.driver.find_element_by_class_name('search-container')
        offering_elems = container.find_elements_by_class_name('menu-offering')
        self.assertEquals(len(offering_elems), len(offering_names))

        for off_elem in offering_elems:
            title = off_elem.find_element_by_css_selector('h2')
            self.assertTrue(title.text in offering_names)

    def test_basic_navigation(self):
        # Build test info
        # Create test directories
        offering_path1 = os.path.join(settings.BASEDIR, 'media/provider__test_offering1__1.0')
        offering_path2 = os.path.join(settings.BASEDIR, 'media/provider__test_offering2__1.0')
        os.makedirs(offering_path1)
        os.makedirs(offering_path2)

        self._dirs_to_remove.append(offering_path1)
        self._dirs_to_remove.append(offering_path2)

        test_icon_path = os.path.join(settings.BASEDIR, 'wstore/defaulttheme/static/assets/img/noimage.png')
        shutil.copy2(test_icon_path, os.path.join(offering_path1, 'image.png'))
        shutil.copy2(test_icon_path, os.path.join(offering_path2, 'image.png'))

        # Load USDL info
        offering1_info = {
            'base_uri': 'http://localhost:8081',
            'image_url': '/media/provider__test_offering1__1.0/image.png',
            'name': 'test_offering1',
            'description': 'test',
            'pricing': {
                'price_model': 'free'
            }
        }
        _fill_offering_description('21000aba8e05ac2115f022ff', offering1_info)

        offering2_info = {
            'base_uri': 'http://localhost:8081',
            'image_url': '/media/provider__test_offering2__1.0/image.png',
            'name': 'test_offering2',
            'description': 'example',
            'pricing': {
                'price_model': 'free'
            }
        }
        _fill_offering_description('31000aba8e05ac2115f022f0', offering2_info)

        # Create indexes
        save_indexes()
        _create_indexes()

        # Start interactions with the GUI
        self.login()
        self.view_all()

        self._check_search_container(['test_offering1', 'test_offering2'])
        self.assertEquals(self.driver.current_url, 'http://localhost:8081/search')

        self.search_keyword('test')

        self._check_search_container(['test_offering1'])
        self.assertEquals(self.driver.current_url, 'http://localhost:8081/search/keyword/test')

        self.open_offering_details('test_offering1')

        self.back()
