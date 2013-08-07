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

from django.conf import settings

from wstore.store_commons.utils.method_request import MethodRequest


def notify_provider(purchase):
    """
        This method is used to notify the service provider
        that his offering has been purchased
    """
    notification_url = purchase.offering.notification_url

    data = {
        'offering': {
            'organization': purchase.offering.owner_organization.name,
            'name': purchase.offering.name,
            'version': purchase.offering.version
        },
        'reference': purchase.ref,
    }

    # Notify the service provider
    if notification_url != '':

        # Check the customer
        if purchase.organization_owned:
            data['customer'] = purchase.owner_organization.name
        else:
            data['customer'] = purchase.customer.username

        body = json.dumps(data)
        headers = {'Content-type': 'application/json'}

        request = MethodRequest('POST', notification_url, body, headers)

        opener = urllib2.build_opener()

        try:
            response = opener.open(request)
        except:
            pass

    # if the oil authentication is enabled, notify the idM the new purchase
    if settings.OILAUTH:
        data['applications'] = purchase.offering.applications

        # Get the customer id for the idm
        if purchase.organization_owned:
            data['customer'] = purchase.owner_organization.actor_id
        else:
            data['customer'] = purchase.customer.userprofile.actor_id

        body = json.dumps(data)
        headers = {'Content-type': 'application/json', 'Authorization': 'Bearer ' + purchase.customer.userprofile.access_token}

        from wstore.social_auth_backend import FIWARE_NOTIFICATION_URL

        request = MethodRequest('POST', FIWARE_NOTIFICATION_URL, body, headers)

        opener = urllib2.build_opener()

        try:
            response = opener.open(request)
        except:
            pass