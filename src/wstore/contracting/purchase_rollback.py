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

import os

from django.conf import settings

from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.search.search_engine import SearchEngine


def rollback(purchase):
    # If the purchase state is paid means that the purchase has been made
    # so the models must not be deleted
    offering = purchase.offering

    if purchase.state != 'paid':

        # Check that the payment has been made
        contract = True
        try:
            contr = purchase.contract
        except:
            contract = False

        to_del = True
        if contract:
            # If the charges field contains any charge means that it is not
            # the first charge so the models cannot be deleted
            if len(contr.charges) > 0:
                purchase.state = 'paid'
                purchase.save()
                to_del = False

        if to_del:
            # Check organization owned
            if purchase.organization_owned:
                org = purchase.owner_organization
                if purchase.offering.pk in org.offerings_purchased:
                    org.offerings_purchased.remove(purchase.offering.pk)
                    org.save()

            # Delete the offering from the user profile
            user_profile = UserProfile.objects.get(user=purchase.customer)
            if purchase.offering.pk in user_profile.offerings_purchased:
                user_profile.offerings_purchased.remove(purchase.offering.pk)
                user_profile.save()

            # Delete the contract
            if contract:
                purchase.contract.delete()
            # Delete the Purchase
            purchase.delete()

    # If the purchase is paid the offering must be included in the customer
    # offerings purchased list
    else:
        if purchase.organization_owned:
            org = purchase.owner_organization
            if not purchase.offering.pk in org.offerings_purchased:
                org.offerings_purchased.append(purchase.offering.pk)
                org.save()
        else:
            profile = purchase.customer.userprofile
            if not purchase.offering.pk in profile.offerings_purchased:
                profile.offerings_purchased.append(purchase.offering.pk)
                profile.save()

    # Update offering indexes: Offering index must be updated in any case
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    se = SearchEngine(index_path)
    se.update_index(offering)


# This class is used as a decorator to avoid inconsistent states in
# purchases models in case of Exception
class PurchaseRollback():
    _funct = None

    def __init__(self, funct):
        self._funct = funct

    def __call__(self, user, offering, org_owned=False, payment_info={}):
        try:
            # Call the decorated function
            result = self._funct(user, offering, org_owned, payment_info)
        except Exception as e:
            if unicode(e) != "This offering can't be purchased" and unicode(e) != 'The offering has been already purchased'\
                    and unicode(e) != 'Invalid payment method' and unicode(e) != 'Invalid credit card info'\
                    and unicode(e) != 'The customer does not have a tax address' and unicode(e) != 'The customer does not have payment info'\
                    and unicode(e) != 'Missing a required field in the tax address. It must contain street, postal, city, province and country'\
                    and unicode(e) != 'Open offerings cannot be purchased' \
                    and unicode(e) != 'You must accept the terms and conditions of the offering to acquire it':

                # Get the purchase
                if org_owned:
                    user_profile = UserProfile.objects.get(user=user)
                    purchase = Purchase.objects.get(owner_organization=user_profile.current_organization, offering=offering)
                else:
                    purchase = Purchase.objects.get(customer=user, offering=offering, organization_owned=False)
                rollback(purchase)

            raise e
        return result
