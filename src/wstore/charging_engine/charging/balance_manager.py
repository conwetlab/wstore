# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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
from urllib2 import HTTPError

from wstore.models import RSS, Organization
from wstore.rss_adaptor.rss_manager_factory import RSSManagerFactory


class BalanceManager(object):

    def __init__(self, purchase):
        self._purchase = purchase
        self._expenditure_used = False

        self._rss = None
        self._expenditure_manager = None

        if len(RSS.objects.all()) > 0:
            self._rss = RSS.objects.all()[0]
            rss_factory = RSSManagerFactory(self._rss)
            self._expenditure_manager = rss_factory.get_expenditure_manager(self._rss.access_token)

    def _make_request(self, method, charge, actor, to_raise=False):
        request_failure = None
        try:
            method(charge, actor)
        except HTTPError as e:
            # Check if it is needed to refresh the access token
            if e.code == 401:
                self._rss._refresh_token()
                self._expenditure_manager.set_credentials(self._rss.access_token)
                try:
                    # The user may be unauthorized, an error occurs, or the
                    # actor balance is not enough
                    method(charge, actor)
                except Exception as e:
                    request_failure = e

            else:
                request_failure = e
        except Exception as e:
            request_failure = e

        if to_raise:
            raise request_failure

        return request_failure

    def check_expenditure_limits(self, price):
        """
        Check if the user can purchase the offering depending on its
        expenditure limits and ir accumulated balance thought the RSS
        """

        if self._rss is None:
            return

        # Check who is the charging actor (user or organization)
        actor = self._purchase.owner_organization

        # Check if the actor has defined expenditure limits
        if not actor.expenditure_limits:
            return

        charge = {
            'currency': self._purchase.contract.pricing_model['general_currency'],
            'amount': price
        }

        request_failure = self._make_request(self._expenditure_manager.check_balance, charge, actor)

        # Raise  the correct failure
        if request_failure:
            if type(request_failure) == HTTPError and request_failure.code == 404\
             and json.loads(request_failure.read())['exceptionId'] == 'SVC3705':
                    raise Exception('There is not enough balance. Check your expenditure limits')
            else:
                raise request_failure

        self._expenditure_used = True

    def update_actor_balance(self, price):

        if self._rss is None:
            return

        # Check who is the charging actor (user or organization)
        if self._purchase.organization_owned:
            actor = self._purchase.owner_organization
        else:
            client = self._purchase.customer
            actor = Organization.objects.get(actor_id=client.userprofile.actor_id)

        charge = {
            'currency': self._purchase.contract.pricing_model['general_currency'],
            'amount': price
        }

        # Check balance
        self._make_request(self._expenditure_manager.update_balance, charge, actor, to_raise=True)

    def has_limits(self):
        return self._expenditure_used
