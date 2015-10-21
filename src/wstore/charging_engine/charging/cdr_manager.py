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

from bson import ObjectId

from django.conf import settings

from wstore.rss_adaptor.rss_adaptor import RSSAdaptorThread
from wstore.rss_adaptor.utils.rss_codes import get_currency_code
from wstore.store_commons.database import get_database_connection
from wstore.models import RSS


class CDRManager(object):

    _purchase = None

    def __init__(self, purchase):
        self._purchase = purchase

    def _generate_cdr_part(self, part, model, cdr_info):
        # Create connection for raw database access
        db = get_database_connection()

        # Take and increment the correlation number using
        # the mongoDB atomic access in order to avoid race
        # problems
        currency = self._purchase.contract.pricing_model['general_currency']

        if cdr_info['rss'].api_version == 1:
            # Version 1 uses a global correlation number
            corr_number = db.wstore_rss.find_and_modify(
                query={'_id': ObjectId(cdr_info['rss'].pk)},
                update={'$inc': {'correlation_number': 1}}
            )['correlation_number']

            currency = get_currency_code(self._purchase.contract.pricing_model['general_currency'])

        else:
            # Version 2 uses a correlation number per provider
            corr_number = db.wstore_organization.find_and_modify(
                query={'_id': ObjectId(self._purchase.owner_organization.pk)},
                update={'$inc': {'correlation_number': 1}}
            )['correlation_number']

        return {
            'provider': cdr_info['provider'],
            'service': cdr_info['service_name'],
            'defined_model': model,
            'correlation': str(corr_number),
            'purchase': self._purchase.ref,
            'offering': cdr_info['offering'],
            'product_class': cdr_info['product_class'],
            'description': cdr_info['description'],
            'cost_currency': currency,
            'cost_value': str(part['value']),
            'tax_currency': currency,
            'tax_value': '0.0',
            'source': '1',
            'operator': '1',
            'country': cdr_info['country_code'],
            'time_stamp': cdr_info['time_stamp'],
            'customer': cdr_info['customer'],
            'event': self._purchase.contract.revenue_class
        }

    def generate_cdr(self, applied_parts, time_stamp, price=None):

        cdrs = []

        # Take the first RSS registered
        rss_collection = RSS.objects.all()

        if len(rss_collection) > 0:
            rss = RSS.objects.all()[0]

            # Get the provider (Organization)
            if rss.api_version == 1:
                provider = settings.STORE_NAME.lower() + '-provider'
            else:
                provider = self._purchase.offering.owner_organization.actor_id

            # Set offering ID
            offering = self._purchase.offering.name + ' ' + self._purchase.offering.version

            # Get the customer
            customer = self._purchase.owner_organization.name

            # Get the country code
            country_code = '1'

            # Get the product class
            if rss.api_version == 1:
                product_class = self._purchase.contract.revenue_class
            else:
                off_model = self._purchase.offering
                product_class = off_model.owner_organization.name + '/' + off_model.name + '/' + off_model.version

            cdr_info = {
                'rss': rss,
                'provider': provider,
                'service_name': offering,
                'offering': offering,
                'country_code': country_code,
                'time_stamp': time_stamp,
                'customer': customer,
                'product_class': product_class
            }

            # If any deduction has been applied the whole payment is
            # included in a single CDR instead of including parts in
            # order to avoid a mismatch between the revenues being shared
            # and the real payment

            if price:
                # Create a payment part representing the whole payment
                aggregated_part = {
                    'value': price,
                    'currency': self._purchase.contract.pricing_model['general_currency']
                }
                cdr_info['description'] = 'Complete Charging event: ' + str(price) + ' ' + self._purchase.contract.pricing_model['general_currency']
                cdrs.append(self._generate_cdr_part(aggregated_part, 'Charging event', cdr_info))

            else:
                # Check the type of the applied parts
                if 'single_payment' in applied_parts:

                    # A cdr is generated for every price part
                    for part in applied_parts['single_payment']:
                        cdr_info['description'] = 'Single payment: ' + part['value'] + ' ' + self._purchase.contract.pricing_model['general_currency']
                        cdrs.append(self._generate_cdr_part(part, 'Single payment event', cdr_info))

                if 'subscription' in applied_parts:

                    # A cdr is generated by price part
                    for part in applied_parts['subscription']:
                        cdr_info['description'] = 'Subscription: ' + part['value'] + ' ' + self._purchase.contract.pricing_model['general_currency'] + ' ' + part['unit']
                        cdrs.append(self._generate_cdr_part(part, 'Subscription event', cdr_info))

                if 'charges' in applied_parts:

                    # A cdr is generated by price part
                    for part in applied_parts['charges']:
                        use_part = {
                            'value': part['price'],
                        }
                        if 'price_function' in part['model']:
                            cdr_info['description'] = part['model']['text_function']
                            use_part['currency'] = self._purchase.contract.pricing_model['general_currency']
                        else:
                            use_part['currency'] = self._purchase.contract.pricing_model['general_currency']

                            # Calculate the total consumption
                            use = 0
                            for sdr in part['accounting']:
                                use += int(sdr['value'])
                            cdr_info['description'] = 'Fee per ' + part['model']['unit'] + ', Consumption: ' + str(use)

                        cdrs.append(self._generate_cdr_part(use_part, 'Pay per use event', cdr_info))

            # Send the created CDRs to the Revenue Sharing System
            r = RSSAdaptorThread(rss, cdrs)
            r.start()
