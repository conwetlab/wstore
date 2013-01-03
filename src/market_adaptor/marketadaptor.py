# -*- coding: utf-8 -*-

# Copyright 2012 Universidad Politécnica de Madrid

# This file is part of Wirecluod.

# Wirecloud is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Wirecloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Wirecloud.  If not, see <http://www.gnu.org/licenses/>.


import urllib2
from urllib2 import HTTPError
from urllib import urlencode
from urlparse import urljoin, urlparse

from lxml import etree

from store_commons.utils.method_request import MethodRequest


class MarketAdaptor(object):

    _marketplace_uri = None
    _session_id = None

    def __init__(self, marketplace_uri, user='store_conwet', passwd='store_conwet'):
        self._marketplace_uri = marketplace_uri
        self._user = user
        self._passwd = passwd

    def authenticate(self):

        opener = urllib2.build_opener()

        # submit field is required
        credentials = urlencode({'j_username': self._user, 'j_password': self._passwd, 'submit': 'Submit'})
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        request = MethodRequest("POST", urljoin(self._marketplace_uri, "/FiwareMarketplace/j_spring_security_check"), credentials, headers)

        parsed_url = None
        try:
            response = opener.open(request)
            parsed_url = urlparse(response.url)

        except HTTPError, e:
            # Marketplace can return an error code but authenticate
            parsed_url = urlparse(e.url)

        if parsed_url[4] != 'login_error' and parsed_url[3][:10] == 'jsessionid':
            # parsed_url[3] params field, contains jsessionid
            self._session_id = parsed_url[3][11:]
        else:
            raise Exception('Marketplace login error')

    def add_store(self, store_info):

        if self._session_id is None:
            self.authenticate()

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + store_info['store_name'] + '" ><url>' + store_info['store_uri'] + '</url></resource>'
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'content-type': 'application/xml', 'Cookie': session_cookie}

        opener = urllib2.build_opener()
        request = MethodRequest("PUT", urljoin(self._marketplace_uri, "registration/store/"), params, headers)
        try:
            response = opener.open(request)
        except HTTPError, e:
            # Marketplace redirects to a login page (sprint_security_login) if
            # the session expires. In addition, python don't follow
            # redirections when issuing DELETE requests, so we have to check for
            # a 302 startus code
            if e.code == 302:
                self._session_id = None
                self.add_store(store_info)
                return
            else:
                raise HTTPError(e.url, e.code, e.msg, None, None)

        if response.code != 201:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def update_store(self, store_info):
        pass

    def delete_store(self, store):

        if self._session_id is None:
            self.authenticate()

        opener = urllib2.build_opener()
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'content-type': 'application/xml', 'Cookie': session_cookie}

        request = MethodRequest("DELETE", urljoin(self._marketplace_uri, "registration/store/" + store), '', headers)

        try:
            response = opener.open(request)
        except HTTPError, e:
            # Marketplace redirects to a login page (sprint_security_login) if
            # the session expires. In addition, python don't follow
            # redirections when issuing DELETE requests, so we have to check for
            # a 302 startus code
            if e.code == 302:
                self._session_id = None
                self.delete_store(store)
                return
            else:
                raise HTTPError(e.url, e.code, e.msg, None, None)

        if response.code != 200:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def add_service(self, store, service_info):

        if self._session_id is None:
            self.authenticate()

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + service_info['name'] + '" ><url>' + service_info['url'] + '</url></resource>'
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'content-type': 'application/xml', 'Cookie': session_cookie}

        opener = urllib2.build_opener()
        request = MethodRequest("PUT", urljoin(self._marketplace_uri, "offering/store/" + store + "/offering"), params, headers)
        try:
            response = opener.open(request)
        except HTTPError, e:
            # Marketplace redirects to a login page (sprint_security_login) if
            # the session expires. In addition, python don't follow
            # redirections when issuing PUT requests, so we have to check for
            # a 302 startus code
            if e.code == 302:
                self._session_id = None
                self.add_service(store, service_info)
                return
            else:
                raise HTTPError(e.url, e.code, e.msg, None, None)

        if response.code != 201:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def update_service(self, store, service_info):
        pass

    def delete_service(self, store, service):

        if self._session_id is None:
            self.authenticate()

        opener = urllib2.build_opener()
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'Cookie': session_cookie}

        request = MethodRequest("DELETE", urljoin(self._marketplace_uri, "offering/store/" + store + "/offering/" + service), '', headers)

        try:
            response = opener.open(request)
        except HTTPError, e:
            # Marketplace redirects to a login page (sprint_security_login) if
            # the session expires. In addition, python don't follow
            # redirections when issuing DELETE requests, so we have to check for
            # a 302 startus code
            if e.code == 302:
                self._session_id = None
                self.delete_service(store, service)
                return
            else:
                raise HTTPError(e.url, e.code, e.msg, None, None)

        if response.code != 200:
            raise HTTPError(response.url, response.code, response.msg, None, None)
