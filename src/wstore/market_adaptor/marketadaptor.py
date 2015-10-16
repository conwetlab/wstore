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

import json
import urllib
import urllib2
from urllib2 import HTTPError
from urlparse import urljoin, urlparse
from base64 import b64encode

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.store_commons.utils.url import url_fix
from wstore.models import Marketplace


def marketadaptor_factory(marketplace, current_user=None):
    """
    Returns the corresponding MarketAdaptor depending on the API version
    """

    adaptors = {
        1: MarketAdaptorV1,
        2: MarketAdaptorV2
    }

    return adaptors[marketplace.api_version](
        marketplace.host,
        user=marketplace.credentials.username,
        passwd=marketplace.credentials.passwd,
        current_user=current_user
    )


class MarketAdaptor():

    _marketplace_uri = None

    def __init__(self, marketplace_uri, user='store_conwet', passwd='store_conwet', current_user=None):
        self._marketplace_uri = marketplace_uri
        self._user = user
        self._passwd = passwd
        self._current_user = current_user

    def _get_store_name(self):
        market = Marketplace.objects.get(host=self._marketplace_uri)
        return market.store_id

    def _get_local_token(self):
        token = b64encode(self._user + ':' + self._passwd)
        return 'Basic ' + token

    def _get_token(self):
        pass

    def _make_request(self, method, url, params, headers, code):
        opener = urllib2.build_opener()

        # Include credentials in the header
        headers['Authorization'] = self._get_token()
        headers['Accept'] = 'application/json'

        request = MethodRequest(method, url, params, headers)
        response = opener.open(request)

        if response.code != code:
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return response

    def add_store(self, store_info):
        pass

    def delete_store(self):
        pass

    def add_service(self, offering):
        pass

    def delete_service(self, service):
        pass


class MarketAdaptorV1(MarketAdaptor):

    def _get_token(self):
        return self._get_local_token()

    def add_store(self, store_info):

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + store_info['store_name'] + '" ><url>' + store_info['store_uri'] + '</url></resource>'
        headers = {'content-type': 'application/xml'}

        url = urljoin(self._marketplace_uri, "v1/registration/store/")
        self._make_request('PUT', url, params, headers, 201)

        return store_info['store_name']

    def delete_store(self):
        store = self._get_store_name()

        url = urljoin(self._marketplace_uri, "v1/registration/store/" + store)

        url = url_fix(url)
        self._make_request('DELETE', url, '', {}, 200)

    def add_service(self, offering):
        store = self._get_store_name()

        offering_id = offering.owner_organization.name + ' ' + offering.name + ' ' + offering.version

        params = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><resource name="' + offering_id + '" ><url>' + offering.description_url + '</url></resource>'
        headers = {'content-type': 'application/xml'}
        url = urljoin(self._marketplace_uri, "v1/offering/store/" + store + "/offering")

        url = url_fix(url)
        self._make_request('PUT', url, params, headers, 201)

        return offering_id

    def delete_service(self, service):
        store = self._get_store_name()

        url = urljoin(self._marketplace_uri, "v1/offering/store/" + store + "/offering/" + service)
        url = url_fix(url)

        self._make_request('DELETE', url, '', {}, 200)


class MarketAdaptorV2(MarketAdaptor):

    def _get_token(self):
        result = None
        if not self._user:
            result = 'Bearer ' + self._current_user.userprofile.access_token
        else:
            result = self._get_local_token()

        return result

    def _get_id(self, response):
        uri = response.headers.getheader('Location')

        if uri.endswith('/'):
            uri = uri[:-1]

        return uri.split('/')[-1]

    def add_store(self, store_info):
        url = urljoin(self._marketplace_uri, "api/v2/store")

        params = {
            'displayName': store_info['store_name'],
            'url': store_info['store_uri'],
            'comment': "WStore instance deployed in " + store_info['store_uri']
        }
        headers = {
            'Content-type': 'application/json'
        }

        response = self._make_request('POST', url, json.dumps(params), headers, 201)

        return self._get_id(response)

    def delete_store(self):
        # Get WStore name in the marketplace
        store = self._get_store_name()

        url = urljoin(self._marketplace_uri, "api/v2/store/" + store)
        url = url_fix(url)
        self._make_request('DELETE', url, '', {}, 204)

    def add_service(self, offering):

        store = self._get_store_name()
        url = urljoin(self._marketplace_uri, "api/v2/store/" + store + "/description")

        # Build Repository URL in order to load resource USDL descriptions
        parsed_url = urlparse(offering.description_url)
        splitted_path = parsed_url.path.split('/')

        # Check repository version
        if 'v2' in splitted_path:
            service_url = parsed_url.scheme + '://' + parsed_url.netloc

            # Check if the webapp name of the repository is included in the path
            if splitted_path.index('v2') > 1:
                service_url += '/' + splitted_path[1]

            query = "CONSTRUCT { ?a ?b ?c . ?d ?e ?f . } WHERE {"
            query += " { GRAPH <%s> { ?a ?b ?c } }" % (offering.get_uri())
            query += " UNION"
            query += " { <%s> <http://www.linked-usdl.org/ns/usdl-core#includes> ?n ." % (offering.get_uri())
            query += " GRAPH ?n { ?d ?e ?f } }}"

            query = urllib.quote_plus(query)

            service_url += '/v2/services/query?query=' + query

        else:
            service_url = offering.description_url

        offering_id = offering.owner_organization.name + ' ' + offering.name + ' ' + offering.version

        params = {
            "displayName": offering_id,
            "url": service_url
        }

        headers = {
            'Content-type': 'application/json'
        }

        response = self._make_request('POST', url, json.dumps(params), headers, 201)

        return self._get_id(response)

    def delete_service(self, service):
        store = self._get_store_name()

        url = urljoin(self._marketplace_uri, "api/v2/store/" + store + "/description/" + service)
        url = url_fix(url)
        self._make_request('DELETE', url, '', {}, 204)
