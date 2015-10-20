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
import json
import shutil
import time
import urllib2

from nose_parameterized import parameterized
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from django.conf import settings
from django.contrib.auth.models import User
from django.test.utils import override_settings

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.store_commons.utils.testing import save_indexes, restore_indexes, save_tags, restore_tags
from wstore.search.search_engine import SearchEngine
from wstore.selenium_tests.testcase import WStoreSeleniumTestCase
from wstore.models import Offering, Purchase
from wstore.social.tagging.tag_manager import TagManager
from wstore.selenium_tests.test_server import TestServer
import unittest


TESTING_PORT = 8989


def _set_offering_organization(pk, owner):
    offering = Offering.objects.get(pk=pk)
    offering.owner_organization = User.objects.get(username=owner).userprofile.current_organization
    offering.save()


def _fill_purchase_org(pk, owner):
    user = User.objects.get(username=owner)
    purchase = Purchase.objects.get(pk=pk)

    user.userprofile.offerings_purchased.append(purchase.offering.pk)
    user.userprofile.save()

    purchase.owner_organization = user.userprofile.current_organization
    purchase.save()


def _fill_provider_role(username):
    user = User.objects.get(username=username)
    orgs = user.userprofile.organizations

    new_org = []
    for o in orgs:
        if o['organization'] == user.userprofile.current_organization.pk:
            o['roles'].append('provider')

        new_org.append(o)

    user.userprofile.organizations = new_org
    user.userprofile.save()


def _create_indexes():
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    search_engine = SearchEngine(index_path)

    for off in Offering.objects.all():
        search_engine.create_index(off)


def _create_tags():
    tm = TagManager()
    offering1 = Offering.objects.get(name='test_offering1')
    offering2 = Offering.objects.get(name='test_offering2')
    offering3 = Offering.objects.get(name='test_offering3')

    tm.update_tags(offering1, ['service', 'tag'])
    tm.update_tags(offering2, ['dataset', 'tag'])
    tm.update_tags(offering3, ['widget'])


@unittest.skipIf('wstore.selenium_tests' not in settings.INSTALLED_APPS, 'Selenium tests not enabled')
class BasicSearchTestCase(WStoreSeleniumTestCase):

    tags = ('selenium', )
    _dirs_to_remove = []

    def __init__(self, methodName='runTest'):
        WStoreSeleniumTestCase.__init__(self, methodName=methodName)
        self.fixtures.extend(['basic_offerings.json'])

    def setUp(self):
        # Fill offering info
        # Create test directories
        offering_path1 = os.path.join(settings.BASEDIR, 'media/provider__test_offering1__1.0')
        offering_path2 = os.path.join(settings.BASEDIR, 'media/provider__test_offering2__1.0')
        offering_path3 = os.path.join(settings.BASEDIR, 'media/provider__test_offering3__1.0')
        os.makedirs(offering_path1)
        os.makedirs(offering_path2)
        os.makedirs(offering_path3)

        self._dirs_to_remove.append(offering_path1)
        self._dirs_to_remove.append(offering_path2)
        self._dirs_to_remove.append(offering_path3)

        test_icon_path = os.path.join(settings.BASEDIR, 'wstore/defaulttheme/static/assets/img/noimage.png')
        shutil.copy2(test_icon_path, os.path.join(offering_path1, 'image.png'))
        shutil.copy2(test_icon_path, os.path.join(offering_path2, 'image.png'))
        shutil.copy2(test_icon_path, os.path.join(offering_path3, 'image.png'))

        _set_offering_organization('21000aba8e05ac2115f022ff', 'provider')
        _set_offering_organization('31000aba8e05ac2115f022f0', 'provider')
        _set_offering_organization('aaaaaaaaaaaaac2115f022f0', 'admin')

        _fill_purchase_org('61006aba8e05ac21bbbbbbbb', 'provider')

        _fill_provider_role('provider')

        # Create indexes
        save_indexes()
        _create_indexes()

        # Create tag indexes
        save_tags()
        _create_tags()

        WStoreSeleniumTestCase.setUp(self)

    def tearDown(self):
        # Remove directories
        for path in self._dirs_to_remove:
            shutil.rmtree(path, ignore_errors=True)

        restore_indexes()
        restore_tags()
        WStoreSeleniumTestCase.tearDown(self)

    def test_offering_search(self):
        # Start interactions with the GUI
        self.login()
        self.view_all()

        # Search by keyword
        self._check_container('search-container', ['test_offering1', 'test_offering2', 'test_offering3'])
        self.assertEquals(self.driver.current_url, 'http://localhost:8081/search')

        self.search_keyword('test')

        self._check_container('search-container', ['test_offering1'])
        self.assertEquals(self.driver.current_url, 'http://localhost:8081/search/keyword/test')

        self.open_offering_details('test_offering1')

        self.back()

        # Search by main categories
        time.sleep(3)
        self.click_first_cat()
        self._check_container('search-container', ['test_offering1'])

        self.click_second_cat()
        self._check_container('search-container', ['test_offering2'])

        self.click_third_cat()
        self._check_container('search-container', ['test_offering3'])

        # Search by tag
        self.view_all()

        self.open_offering_details('test_offering1')
        self.click_tag('tag')
        self._check_container('search-container', ['test_offering1', 'test_offering2'])

        self.logout()

    def test_catalogue_search(self):
        self.login(username='provider')

        # Open my offerings page
        self.click_first_nav()

        # Check purchased offerings
        self._check_container('offerings-container', ['test_offering3'])

        self.click_second_cat()

        # Check provided offerings
        self._check_container('offerings-container', ['test_offering1', 'test_offering2'])

        # Search by keyword
        self.search_keyword('test', id_='#cat-search-input', btn='#cat-search')
        self._check_container('offerings-container', ['test_offering1'])

        self.logout()


class AdministrationTestCase(WStoreSeleniumTestCase):
    pass


@unittest.skipIf('wstore.selenium_tests' not in settings.INSTALLED_APPS, 'Selenium tests not enabled')
class OfferingManagementTestCase(WStoreSeleniumTestCase):

    tags = ('selenium',)

    def __init__(self, methodName='runTest'):
        WStoreSeleniumTestCase.__init__(self, methodName=methodName)
        self.fixtures.extend(['repositories.json'])

    def setUp(self):
        # Start the testing server
        self._server = TestServer()
        self._server.set_port(TESTING_PORT)
        self._server.set_max_request(1)
        self._server.start()
        _fill_provider_role('provider')
        WStoreSeleniumTestCase.setUp(self)

    def tearDown(self):
        # If the server is still waiting for a call make a
        # fake call in order to terminate it
        if self._server.call_received() < self._server.max_request:
            from urllib2 import urlopen
            self._server.set_max_request(0)
            try:
                url = 'http://localhost:' + unicode(TESTING_PORT)
                urlopen(url)
            except:
                pass

        path = os.path.join(settings.BASEDIR, 'media/provider__test_offering__1.0')
        shutil.rmtree(path, ignore_errors=True)

        WStoreSeleniumTestCase.tearDown(self)

    def test_create_offering(self):
        self.login('provider')
        self.click_first_nav()

        self._check_container('offerings-container', [])

        # Create
        self.create_offering_menu()

        self.fill_basic_offering_info({
            'name': 'test_offering',
            'version': '1.0',
            'notification': None,
            'open': False
        })

        self.driver.find_element_by_css_selector('.modal-footer > .btn').click()

        self.fill_usdl_info({
            'description': 'A test offering',
            'abstract': 'test',
            'legal': {
                'title': 'terms and conditions',
                'text': 'An example terms and conditions'
            }
        })

        self.driver.find_element_by_css_selector('.modal-footer > input[value=Next]').click()  # Next
        self.driver.find_element_by_css_selector('.modal-footer > input[value=Next]').click()  # Next

        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-footer > input[value=Accept]"))
        )
        element.click()

        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-footer > .btn"))
        )
        element.click()

        time.sleep(1)
        self.click_second_cat()
        self._check_container('offerings-container', ['test_offering'])

        # Update
        self.open_offering_details('test_offering')

        # Bind
        # Publish


@unittest.skipIf('wstore.selenium_tests' not in settings.INSTALLED_APPS, 'Selenium tests not enabled')
@override_settings(PAYMENT_METHOD=None)
class PurchaseTestCase(WStoreSeleniumTestCase):
    tags = ("selenium", "selenium-purchase")

    def __init__(self, methodName='runTest'):
        WStoreSeleniumTestCase.__init__(self, methodName=methodName)
        self.fixtures.extend(['basic_offerings.json', 'oauth_info.json'])

    def setUp(self):
        # Start the testing server
        self._server = TestServer()
        self._server.set_port(TESTING_PORT)
        self._server.set_max_request(2)
        self._server.start()

        _set_offering_organization('21000aba8e05ac2115f022ff', 'provider')

        WStoreSeleniumTestCase.setUp(self)

    def tearDown(self):
        if self._server.call_received() < self._server.max_request:
            from urllib2 import urlopen
            self._server.set_max_request(0)
            try:
                url = 'http://localhost:' + unicode(TESTING_PORT)
                urlopen(url)
            except:
                pass

        # Remove bills if needed
        for p in Purchase.objects.all():
            for bill in p.bill:
                path = os.path.join(settings.BASEDIR, bill[1:])
                try:
                    os.remove(path)
                except:
                    pass

        WStoreSeleniumTestCase.tearDown(self)

    def get_modal_wait(self, locator):
        def not_present_modal(driver):
            element = False
            try:
                self.driver.implicitly_wait(0)
                driver.find_element_by_id(locator)
            except NoSuchElementException:
                element = driver.find_element_by_css_selector('.btn-danger')
            finally:
                self.driver.implicitly_wait(5)

            return element

        return not_present_modal

    def test_remote_purchase_form(self):

        token = self.oauth2_login()

        # Make API request to initiate the process
        opener = urllib2.build_opener()
        url = self.live_server_url + '/api/contracting/form'

        data = {
            'offering': {
                'organization': 'provider',
                'name': 'test_offering1',
                'version': '1.1'
            },
            'redirect_uri': 'http://localhost:' + unicode(TESTING_PORT)
        }

        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer ' + token
        }
        request = MethodRequest('POST', url, json.dumps(data), headers)

        response = opener.open(request)

        # Redirect browser to the remote purchase form
        form_url = json.loads(response.read())['url']
        self.driver.get(form_url)

        # Select price plan
        self.select_plan('plan1')
        self.driver.find_element_by_css_selector('.modal-footer .btn-basic').click()

        # Accept terms and conditions
        self.accept_conditions()
        self.driver.find_element_by_css_selector('.modal-footer .btn-basic').click()

        # Fill purchase form
        self.fill_tax_address({
            'street': 'fake street',
            'postal': '12345',
            'city': 'fake city',
            'province': 'fake province',
            'country': 'Spain'
        })

        self.driver.find_element_by_css_selector('.modal-footer .btn-basic').click()

        # Wait until the purchase modal dissapears
        WebDriverWait(self.driver, 5).until(self.get_modal_wait('postal'))

        # Close download resources modal
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.modal-footer .btn-basic'))
        ).click()

        # Wait until the dowload modal dissapears
        element = WebDriverWait(self.driver, 5).until(self.get_modal_wait('message'))

        # End the purchase
        element.click()

        # Check redirection
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "hr"))
        )
        expected_url = 'http://localhost:' + unicode(TESTING_PORT) + '/'
        self.assertEquals(self.driver.current_url, expected_url)


@unittest.skipIf('wstore.selenium_tests' not in settings.INSTALLED_APPS, 'Selenium tests not enabled')
class ResourceManagementTestCase(WStoreSeleniumTestCase):

    def __init__(self, methodName='runTest'):
        self.fixtures.extend(['resources.json'])
        WStoreSeleniumTestCase.__init__(self, methodName=methodName)

    @parameterized.expand([
    ])
    def test_register_resource(self, resource_info):
        self.login()
        self.click_first_nav()
        self.register_resource({})
