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

from urlparse import urljoin

from wstore.rss_adaptor.rss_manager import RSSManager


class ExpenditureManager(RSSManager):

    _provider_id = None

    def __init__(self, rss, credentials):
        RSSManager.__init__(self, rss, credentials)

        from django.conf import settings
        self._provider_id = settings.STORE_NAME.lower()

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
        self._refresh_rss()

    def delete_provider_limit(self):
        """
        Delete the expenditure limit of a provider
        """
        endpoint = urljoin(self._rss.host, '/expenditureLimit/limitManagement/' + self._provider_id)
        endpoint += '?service=fiware'
        # Make expenditure request
        self._make_request('DELETE', endpoint)
        self._refresh_rss()

    def set_actor_limit(self, limits, actor_profile):
        """
        Create the expenditure limit of a provider
        """
        currency = limits['currency']
        del(limits['currency'])

        data = {
            'service': 'fiware',
            'limits': [{
                'type': limit,
                'currency': currency,
                'maxAmount': limits[limit]
            } for limit in limits]
        }

        endpoint = urljoin(self._rss.host, '/expenditureLimit/limitManagement/' + self._provider_id + '/' + str(actor_profile.actor_id))
        self._make_request('POST', endpoint, data)

    def check_balance(self, charge, actor_profile):
        """
        Check the balance of an actor in order to determine
        if it has enough balance
        """
        data = {
            'service': 'fiware',
            'appProvider': self._provider_id,
            'currency': charge['currency'],
            'amount': charge['amount'],
            'chargeType': 'C'
        }
        endpoint = urljoin(self._rss.host, 'expenditureLimit/balanceAccumulated/' + str(actor_profile.actor_id))
        self._make_request('POST', endpoint, data)

    def update_balance(self, charge, actor_profile):
        """
        Update  the balance of an actor when it makes a purchase
        """
        data = {
            'service': 'fiware',
            'appProvider': self._provider_id,
            'currency': charge['currency'],
            'amount': charge['amount'],
            'chargeType': 'C'
        }
        endpoint = urljoin(self._rss.host, 'expenditureLimit/balanceAccumulated/' + str(actor_profile.actor_id))
        self._make_request('PUT', endpoint, data)
