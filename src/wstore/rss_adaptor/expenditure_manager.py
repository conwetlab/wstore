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

import json
import urllib2
from urllib2 import HTTPError
from urlparse import urljoin

from wstore.store_commons.utils.method_request import MethodRequest


class ExpenditureManager():

    _rss = None
    _credentials = None
    _provider_id = None

    def __init__(self, rss, credentials):
        self._rss = rss
        self._credentials = credentials

        from django.conf import settings
        self._provider_id = settings.STORE_NAME.lower()

    def _make_request(self, method, url, data={}):
        """
           Makes requests to the RSS
        """
        opener = urllib2.build_opener()

        headers = {
            'content-type': 'application/json',
            'X-Auth-Token': self._credentials
        }
        request = MethodRequest(method, url, json.dumps(data), headers)

        response = opener.open(request)    

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return response

    def set_provider_limit(self):
        """
           Set the expenditure limit of WStore provider in the RSS
        """

        limits = self._rss.expenditure_limits
        currency = limits['currency']
        del(limits['currency'])

        # Build expenditure request
        data = {
            'service': 'fiware',
            'limits': [{
                'type': limit,
                'currency': currency,
                'maxAmount': limits[limit]
            } for limit in limits]
        }
        endpoint = urljoin(self._rss.host, '/expenditureLimit/limitManagement/' + self._provider_id)

        # Make expenditure request
        self._make_request('POST', endpoint, data=data)

    def delete_provider_limit(self):
        endpoint = urljoin(self._rss.host, '/expenditureLimit/limitManagement/' + self._provider_id)
        # Make expenditure request
        self._make_request('DELETE', endpoint)

    def get_provider_limit(self):
        pass

    def set_actor_limit(self):
        pass

    def get_actor_limit(self):
        pass

    def set_credentials(self, credentials):
        self._credentials = credentials
