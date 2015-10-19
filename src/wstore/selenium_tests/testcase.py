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
import time
import urllib2
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.test import TestCase
from django.conf import settings
from django.test.testcases import LiveServerTestCase

from wstore.store_commons.utils.method_request import MethodRequest


class WStoreSeleniumTestCase(TestCase, LiveServerTestCase):

    fixtures = ['selenium_basic.json']

    @classmethod
    def setUpClass(cls):
        super(WStoreSeleniumTestCase, cls).setUpClass()

    def setUp(self):
        # Open the page
        self.driver = WebDriver()
        self.driver.implicitly_wait(5)
        self.driver.set_window_size(1024, 768)
        self.driver.get(self.live_server_url)
        TestCase.setUp(self)

    def _check_container(self, container, offering_names):
        # Check offerings container
        container = self.driver.find_element_by_class_name(container)
        offering_elems = container.find_elements_by_class_name('menu-offering')
        self.assertEquals(len(offering_elems), len(offering_names))

        for off_elem in offering_elems:
            title = off_elem.find_element_by_css_selector('h2')
            self.assertTrue(title.text in offering_names)

    def login(self, username='admin'):
        # Set username
        username_elem = self.driver.find_element_by_name('username')
        username_elem.send_keys(username)

        # Set password
        password_elem = self.driver.find_element_by_name('password')
        password_elem.send_keys('admin')

        # Click login
        self.driver.find_element_by_css_selector('#login-form button').click()

    def oauth2_login(self, username='admin'):
        from wstore.selenium_tests.tests import TESTING_PORT
        self.driver.get(self.live_server_url + '/oauth2/auth?response_type=code&client_id=test_app&redirect_uri=http://localhost:' + unicode(TESTING_PORT))

        self.login(username)

        self.driver.find_element_by_class_name('btn-blue').click()
        time.sleep(1)

        # Get authorization code
        while self._server.call_received() < 1:
            pass

        code = self._server.get_path().split('=')[1]

        # Get access token
        opener = urllib2.build_opener()

        url = self.live_server_url + '/oauth2/token'

        data = 'client_id=test_app'
        data += '&client_secret=secret'
        data += '&grant_type=authorization_code'
        data += '&code=' + code
        data += '&redirect_uri=' + 'http://localhost:' + unicode(TESTING_PORT)

        headers = {
            'content-type': 'application/form-url-encoded',
        }
        request = MethodRequest('POST', url, data, headers)

        response = opener.open(request)

        token = json.loads(response.read())['access_token']

        return token

    def logout(self):
        self.driver.find_element_by_class_name('icon-double-angle-down').click()
        options = self.driver.find_elements_by_css_selector('#settings-menu > li')

        options[-1].click()

    def tearDown(self):
        self.driver.quit()
        TestCase.tearDown(self)

    def back(self):
        self.driver.find_element_by_id('back').click()

    def view_all(self):
        self.driver.find_element_by_css_selector('#all').click()

    def search_keyword(self, keyword, id_='#text-search', btn='#search'):
        # Set search field
        search_elem = self.driver.find_element_by_css_selector(id_)
        search_elem.send_keys(keyword)

        # Click search button
        self.driver.find_element_by_css_selector(btn).click()

    def open_offering_details(self, offering_name):

        elements = self.driver.find_elements_by_class_name('menu-offering')

        for element in elements:
            if element.find_element_by_css_selector('h2').text == offering_name:
                element.click()
                break

    def _get_navs(self):
        submenu = self.driver.find_element_by_class_name('store-sub-menu')
        # Get first element
        return submenu.find_elements_by_css_selector('li')

    def click_first_cat(self):
        self.driver.find_element_by_id('menu-first-text').click()

    def click_second_cat(self):
        self.driver.find_element_by_id('menu-second-text').click()

    def click_third_cat(self):
        self.driver.find_element_by_id('menu-third-text').click()

    def click_first_nav(self):
        self._get_navs()[0].click()

    def click_second_nav(self):
        self._get_navs()[1].click()

    def _open_provider_option(self, option):
        self.driver.find_element_by_css_selector('#provider-options a.btn').click()
        self.driver.find_element_by_id(option).click()

    def create_offering_menu(self):
        self._open_provider_option('create-app')

    def fill_basic_offering_info(self, offering_info):
        # Name and version
        self.driver.find_element_by_css_selector('[name="app-name"]').send_keys(offering_info['name'])
        self.driver.find_element_by_css_selector('[name="app-version"]').send_keys(offering_info['version'])

        # Select the notification URL option
        if not offering_info['notification']:
            self.driver.find_element_by_css_selector('input[type="radio"][value="none"]').click()
        elif offering_info['notification'] == 'default':
            self.driver.find_element_by_css_selector('input[type="radio"][value="default"]').click()
        else:
            self.driver.find_element_by_css_selector('input[type="radio"][value="new"]').click()
            self.driver.find_element_by_id('notify').send_keys(offering_info['notification'])

        # Add the logo
        logo_path = os.path.join(settings.BASEDIR, 'wstore/defaulttheme/static/assets/img/noimage.png')
        self.driver.find_element_by_id('img-logo').send_keys(logo_path)

        # Mark as open if needed
        if offering_info['open']:
            self.driver.find_element_by_id('open-offering').click()

    def fill_usdl_info(self, usdl_info):
        # Fill description field
        self.driver.find_element_by_id('description').send_keys(usdl_info['description'])
        self.driver.find_element_by_id('abstract').send_keys(usdl_info['abstract'])

        if 'legal' in usdl_info:
            self.driver.find_element_by_id('legal-title').send_keys(usdl_info['legal']['title'])
            self.driver.find_element_by_id('legal-text').send_keys(usdl_info['legal']['text'])

    def register_resource(self, resource_info):
        pass

    def click_tag(self, tag):
        tag_elems = self.driver.find_elements_by_class_name('tag')

        for te in tag_elems:
            if te.text == tag:
                te.click()
                break

    def fill_tax_address(self, tax):
        # Wait until the form is loaded
        element = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "street"))
        )
        element.send_keys(tax['street'])
        self.driver.find_element_by_id('postal').send_keys(tax['postal'])
        self.driver.find_element_by_id('city').send_keys(tax['city'])
        self.driver.find_element_by_id('province').send_keys(tax['province'])
        self.driver.find_element_by_id('country').send_keys(tax['country'])
