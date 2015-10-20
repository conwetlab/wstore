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

import paypalrestsdk

from django.contrib.sites.models import Site

from wstore.charging_engine.payment_client.payment_client import PaymentClient


# Paypal creadetials
PAYPAL_CLIENT_ID = 'AVOLRuc4jN599UD5FMLHv07T7pnmh76zrllx60cQ-fPK39Bu4yR2iOCzNrzqou6XmAFbnuYhdMY4cExY'
PAYPAL_CLIENT_SECRET = 'EAgeaOxAgJ5ZMMu9Tf4riICdT7Sz2y77PRBwUIYppNlf_xw2Q0WD1_jCG4YzSLNxQFevkNnFovtT02u7'
MODE = 'sandbox'  # sandbox or live


class PayPalClient(PaymentClient):

    _purchase = None
    _checkout_url = None

    def __init__(self, purchase):
        self._purchase = purchase
        # Configure API connection
        paypalrestsdk.configure({
            "mode": MODE,
            "client_id": PAYPAL_CLIENT_ID,
            "client_secret": PAYPAL_CLIENT_SECRET
        })

    def start_redirection_payment(self, price, currency):
        # Build URL
        url = Site.objects.all()[0].domain
        if url[-1] != '/':
            url += '/'

        # Build payment object
        payment = paypalrestsdk.Payment({
            'intent': 'sale',
            'payer': {
                'payment_method': 'paypal'
            },
            'redirect_urls': {
                'return_url': url + 'api/contracting/' + self._purchase.ref + '/accept',
                'cancel_url': url + 'api/contracting/' + self._purchase.ref + '/cancel'
            },
            'transactions': [{
                'amount': {
                    'total': unicode(price),
                    'currency': currency
                },
                'description': 'Payment related to the offering: ' + self._purchase.offering.owner_organization.name + ' ' + self._purchase.offering.name + ' version ' + self._purchase.offering.version
            }]
        })

        # Create Payment
        if not payment.create():
            raise Exception("The payment cannot be created: " + payment.error)

        # Extract URL where redirecting the customer
        response = payment.to_dict()
        for l in response['links']:
            if l['rel'] == 'approval_url':
                self._checkout_url = l['href']
                break

    def direct_payment(self, currency, price, credit_card):
        pass

    def end_redirection_payment(self, token, payer_id):
        payment = paypalrestsdk.Payment.find(token)

        if not payment.execute({"payer_id": payer_id}):
            raise Exception("The payment cannot be executed: " + payment.error)

    def get_checkout_url(self):
        return self._checkout_url
