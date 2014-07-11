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

import os
from datetime import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore import charging_engine
from wstore.contracting.purchase_rollback import PurchaseRollback
from wstore.contracting.notify_provider import notify_provider
from wstore.search.search_engine import SearchEngine


@PurchaseRollback
def create_purchase(user, offering, org_owned=False, payment_info=None):

    if offering.state != 'published':
        raise PermissionDenied("This offering can't be purchased")

    if offering.open:
        raise PermissionDenied('Open offerings cannot be purchased')

    profile = UserProfile.objects.get(user=user)

    # Check if the offering is already purchased
    if (org_owned and offering.pk in profile.current_organization.offerings_purchased) \
    or (not org_owned and offering.pk in profile.offerings_purchased):
            raise Exception('The offering has been already purchased')

    organization = profile.current_organization

    plan = None
    # Check the selected plan
    if payment_info and 'plan' in payment_info:
        plan = payment_info['plan']

    # Get the effective tax address
    if not 'tax_address' in payment_info:
        if org_owned:
            tax = organization.tax_address
        else:
            tax = profile.tax_address

        # Check that the customer has a tax address
        if not 'street' in tax:
            raise Exception('The customer does not have a tax address')
    else:
        tax = payment_info['tax_address']

        # Check tax_address fields
        if (not 'street' in tax) or (not 'postal' in tax) or (not 'city' in tax) or (not 'country' in tax):
            raise Exception('The tax address is not valid')

    # Check the payment method before purchase creation in order to avoid
    # an inconsistent state in the database
    credit_card_info = None
    if payment_info['payment_method'] == 'credit_card':
        if 'credit_card' in payment_info:
            # Check credit card info
            if (not ('number' in payment_info['credit_card'])) or (not ('type' in payment_info['credit_card']))\
            or (not ('expire_year' in payment_info['credit_card'])) or (not ('expire_month' in payment_info['credit_card']))\
            or (not ('cvv2' in payment_info['credit_card'])):
                raise Exception('Invalid credit card info')

            credit_card_info = payment_info['credit_card']
        else:
            if org_owned:
                credit_card_info = organization.payment_info
            else:
                credit_card_info = profile.payment_info

            # Check the credit card info
            if not 'number' in credit_card_info:
                raise Exception('The customer does not have payment info')

    elif payment_info['payment_method'] != 'paypal':
        raise ValueError('Invalid payment method')

    # Create the purchase
    purchase = Purchase.objects.create(
        customer=user,
        date=datetime.now(),
        offering=offering,
        organization_owned=org_owned,
        state='pending',
        tax_address=tax,
        owner_organization = organization
    )

    # Load ref
    purchase.ref = purchase.pk
    purchase.save()

    if credit_card_info != None:
        charging_engine = ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card_info, plan=plan)
    else:
        charging_engine = ChargingEngine(purchase, payment_method='paypal', plan=plan)

    redirect_url = charging_engine.resolve_charging(new_purchase=True)

    if redirect_url == None:
        result = purchase

        # If no redirect URL is provided the purchase has ended so the user profile
        # info is updated
        if org_owned:
            organization.offerings_purchased.append(offering.pk)
            organization.save()
        else:
            profile.offerings_purchased.append(offering.pk)
            profile.save()

        notify_provider(purchase)

    else:
        result = redirect_url

    # Update offering indexes
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    se = SearchEngine(index_path)
    se.update_index(offering)

    return result
