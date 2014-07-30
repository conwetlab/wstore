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

from selenium.webdriver.firefox.webdriver import WebDriver

from django.test import TestCase
from django.test.testcases import LiveServerTestCase

class WStoreSeleniumTestCase(TestCase, LiveServerTestCase):

    fixtures = ['selenium_basic.json']

    @classmethod
    def setUpClass(cls):
        super(WStoreSeleniumTestCase, cls).setUpClass()

    def setUp(self):
        # Open the page
        self.driver = WebDriver()
        self.driver.implicitly_wait(5)
        self.driver.get(self.live_server_url)
        TestCase.setUp(self)

    def login(self, username='admin'):
        # Set username
        username_elem = self.driver.find_element_by_name('username')
        username_elem.send_keys(username)

        # Set password
        password_elem = self.driver.find_element_by_name('password')
        password_elem.send_keys('admin')

        # Click login
        self.driver.find_element_by_css_selector('#login-form button').click()

    def tearDown(self):
        self.driver.quit()
        TestCase.tearDown(self)

    def back(self):
        self.driver.find_element_by_id('back').click()

    def view_all(self):
        self.driver.find_element_by_css_selector('#all').click()

    def search_keyword(self, keyword):
        # Set search field
        search_elem = self.driver.find_element_by_css_selector('#text-search')
        search_elem.send_keys(keyword)

        # Click search button
        self.driver.find_element_by_css_selector('#search').click()

    def select_main_menu(self, option):
        pass

    def open_offering_details(self, offering_name):

        elements = self.driver.find_elements_by_class_name('menu-offering')

        for element in elements:
            if element.find_element_by_css_selector('h2').text == offering_name:
                element.click()
                break
