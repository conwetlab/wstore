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

import urllib2
from urllib2 import HTTPError
from urllib import urlencode
from urlparse import urljoin, urlparse

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.store_commons.utils.url import url_fix


def marketadaptor_factory(marketplace):
    """
    Returns the corresponding MarketAdaptor depending on the API version
    """

    adaptors = {
        1: MarketAdaptorV1,
        2: MarketAdaptorV2
    }

    return adaptors[marketplace.api_version](marketplace.host)


class MarketAdaptor():

    def add_store(self, store_info):
        pass

    def delete_store(self, store):
        pass

    def add_service(self, store, service_info):
        pass

    def delete_service(self, store, service):
        pass


class MarketAdaptorV1(MarketAdaptor):

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

        market_path = urlparse(self._marketplace_uri)[2].split('/')[1]
        request = MethodRequest("POST", urljoin(self._marketplace_uri, "/" + market_path + "/j_spring_security_check"), credentials, headers)

        parsed_url = None
        try:
            response = opener.open(request)
            parsed_url = urlparse(response.url)

        except HTTPError, e:
            # Marketplace can return an error code but authenticate
            parsed_url = urlparse(e.filename)

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
        request = MethodRequest("PUT", urljoin(self._marketplace_uri, "v1/registration/store/"), params, headers)
        try:
            response = opener.open(request)
        except HTTPError, e:
            # Marketplace redirects to a login page (sprint_security_login) if
            # the session expires. In addition, python don't follow
            # redirections when issuing DELETE requests, so we have to check for
            # a 302 status code
            if e.code == 302:
                self._session_id = None
                self.add_store(store_info)
                return
            else:
                raise e

        if response.code != 201:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def delete_store(self, store):

        if self._session_id is None:
            self.authenticate()

        opener = urllib2.build_opener()
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'content-type': 'application/xml', 'Cookie': session_cookie}
        url = urljoin(self._marketplace_uri, "v1/registration/store/" + store)

        url = url_fix(url)

        request = MethodRequest("DELETE", url, '', headers)

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
                raise e

        if response.code != 200:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def add_service(self, store, service_info):

        if self._session_id is None:
            self.authenticate()

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + service_info['name'] + '" ><url>' + service_info['url'] + '</url></resource>'
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'content-type': 'application/xml', 'Cookie': session_cookie}
        url = urljoin(self._marketplace_uri, "v1/offering/store/" + store + "/offering")

        url = url_fix(url)

        opener = urllib2.build_opener()
        request = MethodRequest("PUT", url, params, headers)
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
                raise e

        if response.code != 201:
            raise HTTPError(response.url, response.code, response.msg, None, None)

    def delete_service(self, store, service):

        if self._session_id is None:
            self.authenticate()

        opener = urllib2.build_opener()
        session_cookie = 'JSESSIONID=' + self._session_id + ';' + ' Path=/FiwareMarketplace'
        headers = {'Cookie': session_cookie}
        url = urljoin(self._marketplace_uri, "v1/offering/store/" + store + "/offering/" + service)

        url = url_fix(url)

        request = MethodRequest("DELETE", url, '', headers)

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
                raise e

        if response.code != 200:
            raise HTTPError(response.url, response.code, response.msg, None, None)


class MarketAdaptorV2(MarketAdaptor):
    pass
