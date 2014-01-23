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


from paypalpy import paypal

from django.contrib.sites.models import Site

from wstore.charging_engine.payment_client.payment_client import PaymentClient


# Paypal creadetials
PAYPAL_USER = 'un_api1.email.com'
PAYPAL_PASSWD = '1365179727'
PAYPAL_SIGNATURE = 'An5ns1Kso7MWUdW4ErQKJJJ4qi4-A0JFrwdSv9Vm9zAsPyCXQAvP7TqL'
PAYPAL_URL = 'https://api-3t.sandbox.paypal.com/nvp'
PAYPAL_CHECKOUT_URL='https://www.sandbox.paypal.com/webscr?cmd=_express-checkout'

class PayPalClient(PaymentClient):

    _purchase = None
    _client = None
    _response = None

    def __init__(self, purchase):
        self._purchase = purchase
        paypal.SKIP_AMT_VALIDATION = True
        self._client = paypal.PayPal(PAYPAL_USER, PAYPAL_PASSWD, PAYPAL_SIGNATURE, PAYPAL_URL)

    def _get_country_code(self, country):

        country_code = None
        # Get country code
        for cc in paypal.COUNTRY_CODES:
            if cc[1].lower() == country.lower():
                country_code = cc[0]
                break

        return country_code

    def start_redirection_payment(self, price, currency):
        # Set express checkout
        url = Site.objects.all()[0].domain
        if url[-1] != '/':
            url += '/'

        try:
            self._response = self._client.SetExpressCheckout(
                paymentrequest_0_paymentaction='Sale',
                paymentrequest_0_amt=price,
                paymentrequest_0_currencycode=currency,
                returnurl=url + 'api/contracting/' + self._purchase.ref + '/accept',
                cancelurl=url + 'api/contracting/' + self._purchase.ref + '/cancel',
            )

        except Exception, e:
            raise Exception('Error while creating payment: ' + e.value[0])

    def direct_payment(self, currency, price, credit_card):

        country_code = self._get_country_code(self._purchase.tax_address['country'])

        if country_code == None:
            raise Exception('Country not recognized')
        try:
            self._response = self._client.DoDirectPayment(
                paymentaction='Sale',
                ipaddress='192.168.1.1',
                creditcardtype=credit_card['type'],
                acct=credit_card['number'],
                expdate=paypal.ShortDate(int(credit_card['expire_year']), int(credit_card['expire_month'])),
                cvv2=credit_card['cvv2'],
                firstname=self._purchase.customer.first_name,
                lastname=self._purchase.customer.last_name,
                street=self._purchase.tax_address['street'],
                state='mad',
                city=self._purchase.tax_address['city'],
                countrycode=country_code,
                zip=self._purchase.tax_address['postal'],
                amt=price,
                currencycode=currency
            )
        except Exception, e:
            raise Exception('Error while creating payment: ' + e.value[0])

    def end_redirection_payment(self, token, payer_id):
        self._client.DoExpressCheckoutPayment(
            paymentrequest_0_paymentaction='Sale',
            paymentrequest_0_amt=self._purchase.contract.pending_info['price'],
            paymentrequest_0_currencycode='EUR',
            token=token,
            payerid=payer_id
        )

    def get_checkout_url(self):
        return PAYPAL_CHECKOUT_URL + '&token=' + self._response['TOKEN'][0]