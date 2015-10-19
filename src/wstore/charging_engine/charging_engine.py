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

from __future__ import absolute_import

import os
import json
import time
import codecs
import subprocess
import threading
from bson import ObjectId
from urllib2 import HTTPError

from datetime import datetime
from paypalpy import paypal

from django.conf import settings
from django.template import loader, Context
from django.contrib.auth.models import User

from wstore.models import Resource, Organization
from wstore.models import UserProfile, Context as WStore_context
from wstore.models import Purchase
from wstore.models import Offering
from wstore.models import RSS
from wstore.charging_engine.models import Contract
from wstore.charging_engine.models import Unit
from wstore.charging_engine.price_resolver import PriceResolver
from wstore.contracting.purchase_rollback import rollback
from wstore.rss_adaptor.rss_adaptor import RSSAdaptorThread
from wstore.rss_adaptor.utils.rss_codes import get_country_code, get_curency_code
from wstore.rss_adaptor.rss_manager_factory import RSSManagerFactory
from wstore.store_commons.database import get_database_connection


class ChargingEngine:

    _price_model = None
    _purchase = None
    _payment_method = None
    _credit_card_info = None
    _plan = None

    def __init__(self, purchase, payment_method=None, credit_card=None, plan=None):
        self._purchase = purchase
        if payment_method is not None:

            if payment_method != 'paypal':
                if payment_method != 'credit_card':
                    raise Exception('Invalid payment method')
                else:
                    if credit_card is None:
                        raise Exception('No credit card provided')
                    self._credit_card_info = credit_card

            self._payment_method = payment_method

        if plan:
            self._plan = plan

        self._expenditure_used = False

    def _timeout_handler(self):

        db = get_database_connection()

        # Uses an atomic operation to get and set the _lock value in the purchase
        # document
        pre_value = db.wstore_purchase.find_and_modify(
            query={'_id': ObjectId(self._purchase.pk)},
            update={'$set': {'_lock': True}}
        )

        # If _lock not exists or is set to false means that this function has
        # acquired the resource
        if '_lock' not in pre_value or not pre_value['_lock']:

            # Only rollback if the state is pending
            if pre_value['state'] == 'pending':
                # Refresh the purchase
                purchase = Purchase.objects.get(pk=self._purchase.pk)
                rollback(purchase)

            db.wstore_purchase.find_and_modify(
                query={'_id': ObjectId(self._purchase.pk)},
                update={'$set': {'_lock': False}}
            )

    def _fix_price(self, price):

        price = str(price)

        if price.find('.') != -1:
            splited_price = price.split('.')

            if len(splited_price[1]) > 2:
                price = splited_price[0] + '.' + splited_price[1][:2]
            elif len(splited_price[1]) < 2:
                price = price + '0'

        return price

    def _get_country_code(self, country):

        country_code = None
        # Get country code
        for cc in paypal.COUNTRY_CODES:
            if cc[1].lower() == country.lower():
                country_code = cc[0]
                break

        return country_code

    def _charge_client(self, price, concept, currency):

        # Load payment client
        cln_str = settings.PAYMENT_CLIENT
        client_class = cln_str.split('.')[-1]
        client_package = cln_str.partition('.' + client_class)[0]

        payment_client = getattr(__import__(client_package, globals(), locals(), [client_class], -1), client_class)

        # build the payment client
        client = payment_client(self._purchase)
        price = self._fix_price(price)

        if self._payment_method == 'credit_card':
            client.direct_payment(currency, price, self._credit_card_info)
            self._purchase.state = 'paid'

        elif self._payment_method == 'paypal':
            client.start_redirection_payment(price, currency)

            checkout_url = client.get_checkout_url()

            if checkout_url:
                # Set timeout for PayPal transaction to 5 minutes
                t = threading.Timer(300, self._timeout_handler)
                t.start()

                return checkout_url
            else:
                self._purchase.state = 'paid'
        else:
            raise Exception('Invalid payment method')

    def _generate_cdr_part(self, part, model, cdr_info):
        # Create connection for raw database access
        db = get_database_connection()

        # Take and increment the correlation number using
        # the mongoDB atomic access in order to avoid race
        # problems
        currency = self._price_model['general_currency']

        if cdr_info['rss'].api_version == 1:
            # Version 1 uses a global correlation number
            corr_number = db.wstore_rss.find_and_modify(
                query={'_id': ObjectId(cdr_info['rss'].pk)},
                update={'$inc': {'correlation_number': 1}}
            )['correlation_number']

            currency = get_curency_code(self._price_model['general_currency'])

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

    def _generate_cdr(self, applied_parts, time_stamp, price=None):

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
            try:
                country_code = self._get_country_code(self._purchase.tax_address['country'])
                country_code = get_country_code(country_code)
            except:
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
                    'currency': self._price_model['general_currency']
                }
                cdr_info['description'] = 'Complete Charging event: ' + str(price) + ' ' + self._price_model['general_currency']
                cdrs.append(self._generate_cdr_part(aggregated_part, 'Charging event', cdr_info))

            else:
                # Check the type of the applied parts
                if 'single_payment' in applied_parts:

                    # A cdr is generated for every price part
                    for part in applied_parts['single_payment']:
                        cdr_info['description'] = 'Single payment: ' + part['value'] + ' ' + self._price_model['general_currency']
                        cdrs.append(self._generate_cdr_part(part, 'Single payment event', cdr_info))

                if 'subscription' in applied_parts:

                    # A cdr is generated by price part
                    for part in applied_parts['subscription']:
                        cdr_info['description'] = 'Subscription: ' + part['value'] + ' ' + self._price_model['general_currency'] + ' ' + part['unit']
                        cdrs.append(self._generate_cdr_part(part, 'Subscription event', cdr_info))

                if 'charges' in applied_parts:

                    # A cdr is generated by price part
                    for part in applied_parts['charges']:
                        use_part = {
                            'value': part['price'],
                        }
                        if 'price_function' in part['model']:
                            cdr_info['description'] = part['model']['text_function']
                            use_part['currency'] = self._price_model['general_currency']
                        else:
                            use_part['currency'] = self._price_model['general_currency']

                            # Calculate the total consumption
                            use = 0
                            for sdr in part['accounting']:
                                use += int(sdr['value'])
                            cdr_info['description'] = 'Fee per ' + part['model']['unit'] + ', Consumption: ' + str(use)

                        cdrs.append(self._generate_cdr_part(use_part, 'Pay per use event', cdr_info))

            # Send the created CDRs to the Revenue Sharing System
            r = RSSAdaptorThread(rss, cdrs)
            r.start()

    def _generate_invoice(self, price, applied_parts, type_):

        parts = None
        currency = self._purchase.contract.pricing_model['general_currency']
        if type_ == 'initial':
            # If initial can only contain single payments and subscriptions
            parts = {
                'single_parts': [],
                'subs_parts': []
            }
            if 'single_payment' in applied_parts:
                for part in applied_parts['single_payment']:
                    parts['single_parts'].append((part['label'], part['value'], currency))

            if 'subscription' in applied_parts:
                for part in applied_parts['subscription']:
                    parts['subs_parts'].append((part['label'], part['value'], currency, part['unit'], str(part['renovation_date'])))

            # Get the bill template
            bill_template = loader.get_template('contracting/bill_template_initial.html')

        elif type_ == 'renovation':
            parts = {
                'subs_parts': [],
                'subs_subtotal': 0
            }
            # If renovation, It contains subscriptions
            for part in applied_parts['subscription']:
                parts['subs_parts'].append((part['label'], part['value'], currency, part['unit'], str(part['renovation_date'])))
                parts['subs_subtotal'] += float(part['value'])

            # Check use based charges
            if 'charges' in applied_parts and len(applied_parts['charges']) > 0:
                parts['use_parts'] = []
                parts['use_subtotal'] = 0

                # Fill use tuples for the invoice
                for part in applied_parts['charges']:
                    model = part['model']
                    if 'price_function' in model:
                        unit = 'price function'
                        value_unit = model['text_function']
                        use = '- '
                    else:
                        unit = model['unit']
                        value_unit = model['value']

                        # Aggregate use made
                        use = 0
                        for sdr in part['accounting']:
                            use += int(sdr['value'])

                    parts['use_parts'].append((model['label'], unit, value_unit, use, part['price']))
                    parts['use_subtotal'] += part['price']

            # Check deductions
            if 'deductions' in applied_parts and len(applied_parts['deductions']) > 0:
                parts['deduct_parts'] = []
                parts['deduct_subtotal'] = 0

                # Fill use tuples for the invoice
                for part in applied_parts['deductions']:
                    model = part['model']
                    if 'price_function' in model:
                        unit = 'price function'
                        value_unit = model['text_function']
                        use = '- '
                    else:
                        unit = model['unit']
                        value_unit = model['value']

                        # Aggregate use made
                        use = 0
                        for sdr in part['accounting']:
                            use += int(sdr['value'])

                    parts['deduct_parts'].append((model['label'], unit, value_unit, use, part['price']))
                    parts['deduct_subtotal'] += part['price']

            # Get the bill template
            bill_template = loader.get_template('contracting/bill_template_renovation.html')

        elif type_ == 'use':
            # If use, can only contain pay per use parts or deductions
            parts = {
                'use_parts': [],
                'use_subtotal': 0
            }
            for part in applied_parts['charges']:
                model = part['model']
                if 'price_function' in model:
                    unit = 'price function'
                    value_unit = model['text_function']
                    use = '- '
                else:
                    unit = model['unit']
                    value_unit = model['value']

                    # Aggregate use made
                    use = 0
                    for sdr in part['accounting']:
                        use += int(sdr['value'])

                parts['use_parts'].append((model['label'], unit, value_unit, use, part['price']))
                parts['use_subtotal'] += part['price']

            # Check deductions
            if len(applied_parts['deductions']) > 0:
                parts['deduct_parts'] = []
                parts['deduct_subtotal'] = 0

                # Fill use tuples for the invoice
                for part in applied_parts['deductions']:
                    model = part['model']
                    if 'price_function' in model:
                        unit = 'price function'
                        value_unit = model['text_function']
                        use = '- '
                    else:
                        unit = model['unit']
                        value_unit = model['value']

                        # Aggregate use made
                        use = 0
                        for sdr in part['accounting']:
                            use += int(sdr['value'])

                    parts['deduct_parts'].append((model['label'], unit, value_unit, use, part['price']))
                    parts['deduct_subtotal'] += part['price']

            # Get the bill template
            bill_template = loader.get_template('contracting/bill_template_use.html')

        tax = self._purchase.tax_address

        # Render the bill template
        offering = self._purchase.offering
        customer = self._purchase.customer

        customer_profile = UserProfile.objects.get(user=customer)

        resources = []
        for res in offering.resources:
            r = Resource.objects.get(pk=str(res))
            resources.append((r.name, r.description))

        last_charge = self._purchase.contract.last_charge

        if last_charge is None:
            # If last charge is None means that it is the invoice generation
            # associated with a free offering
            date = str(datetime.now()).split(' ')[0]
        else:
            date = str(last_charge).split(' ')[0]

        # Load pricing info into the context
        context = {
            'BASEDIR': settings.BASEDIR,
            'offering_name': offering.name,
            'off_organization': offering.owner_organization.name,
            'off_version': offering.version,
            'ref': self._purchase.ref,
            'date': date,
            'organization': customer_profile.current_organization.name,
            'customer': customer_profile.complete_name,
            'address': tax.get('street'),
            'postal': tax.get('postal'),
            'city': tax.get('city'),
            'province': tax.get('province'),
            'country': tax.get('country'),
            'taxes': [],
            'subtotal': price,  # TODO price without taxes
            'tax': '0',
            'total': price,
            'resources': resources,
            'cur': currency  # General currency of the invoice
        }

        # Include the corresponding parts in the context
        # depending on the type of applied parts
        # Initial Charge
        if type_ == 'initial':
            context['exists_single'] = False
            context['exists_subs'] = False

            if len(parts['single_parts']) > 0:
                context['single_parts'] = parts['single_parts']
                context['exists_single'] = True

            if len(parts['subs_parts']) > 0:
                context['subs_parts'] = parts['subs_parts']
                context['exists_subs'] = True

        # Renovation Charge
        elif type_ == 'renovation':

            context['subs_parts'] = parts['subs_parts']
            context['subs_subtotal'] = parts['subs_subtotal']

            if 'use_parts' in parts:
                context['use'] = True
                context['use_parts'] = parts['use_parts']
                context['use_subtotal'] = parts['use_subtotal']
            else:
                context['use'] = False

            if 'deduct_parts' in parts:
                context['deduction'] = True
                context['deduct_parts'] = parts['deduct_parts']
                context['deduct_subtotal'] = parts['deduct_subtotal']
            else:
                context['deduction'] = False

        # Use based charge
        else:
            context['use_parts'] = parts['use_parts']
            context['use_subtotal'] = parts['use_subtotal']

            if 'deduct_parts' in parts:
                context['deduction'] = True
                context['deduct_parts'] = parts['deduct_parts']
                context['deduct_subtotal'] = parts['deduct_subtotal']
            else:
                context['deduction'] = False

        bill_code = bill_template.render(Context(context))

        # Create the bill code file
        invoice_name = self._purchase.ref + '_' + date
        bill_path = os.path.join(settings.BILL_ROOT, invoice_name + '.html')
        f = codecs.open(bill_path, 'wb', 'utf-8')
        f.write(bill_code)
        f.close()

        in_name = bill_path[:-4] + 'pdf'

        if os.path.exists(in_name):
            in_name = bill_path[:-5] + '_1.pdf'
            invoice_name += '_1'

        # Compile the bill file
        try:
            subprocess.call([settings.BASEDIR + '/create_invoice.sh', bill_path, in_name])
        except:
            raise Exception('Invoice generation problem')

        # Remove temporal files
        for file_ in os.listdir(settings.BILL_ROOT):

            if not file_.endswith('.pdf'):
                os.remove(os.path.join(settings.BILL_ROOT, file_))

        # Load bill path into the purchase
        self._purchase.bill.append(os.path.join(settings.MEDIA_URL, 'bills/' + invoice_name + '.pdf'))

        self._purchase.save()

    def _create_purchase_contract(self):
        # Generate the pricing model structure
        offering = self._purchase.offering
        parsed_usdl = offering.offering_description

        usdl_pricing = {}
        price_model = {}
        # Search and validate the corresponding price plan
        if len(parsed_usdl['pricing']['price_plans']) > 0:
            if len(parsed_usdl['pricing']['price_plans']) == 1:
                usdl_pricing = parsed_usdl['pricing']['price_plans'][0]
            else:
                # A plan must have been specified
                if not self._plan:
                    raise Exception('The price plan label is required to identify the plan')

                # Search the plan
                found = False
                for plan in parsed_usdl['pricing']['price_plans']:
                    if plan['label'].lower() == self._plan.lower():
                        usdl_pricing = plan
                        found = True
                        price_model['label'] = plan['label'].lower()
                        break

                # Validate the specified plan
                if not found:
                    raise Exception('The specified plan does not exist')

        # Save the general currency of the offering
        if 'price_components' in usdl_pricing or 'deductions' in usdl_pricing:
            price_model['general_currency'] = usdl_pricing['currency']

        if 'price_components' in usdl_pricing:

            for comp in usdl_pricing['price_components']:

                # Check if the price component defines a price function
                if 'price_function' in comp:
                    # Price functions always define pay-per-use models
                    if 'pay_per_use' not in price_model:
                        price_model['pay_per_use'] = []

                    price_model['pay_per_use'].append(comp)
                    continue

                # Check price component unit
                try:
                    unit = Unit.objects.get(name=comp['unit'])
                except:
                    raise(Exception, 'Unsupported unit in price plan model')

                # The price component defines a single payment
                if unit.defined_model == 'single payment':
                    if 'single_payment' not in price_model:
                        price_model['single_payment'] = []

                    price_model['single_payment'].append(comp)

                # The price component defines a subscription
                elif unit.defined_model == 'subscription':
                    if 'subscription' not in price_model:
                        price_model['subscription'] = []

                    price_model['subscription'].append(comp)

                # The price component defines a pay per use
                elif unit.defined_model == 'pay per use':
                    if 'pay_per_use' not in price_model:
                        price_model['pay_per_use'] = []

                    price_model['pay_per_use'].append(comp)

        if 'deductions' in usdl_pricing:

            for deduct in usdl_pricing['deductions']:

                if 'deductions' not in price_model:
                    price_model['deductions'] = []

                if 'price_function' not in deduct:
                    unit = Unit.objects.get(name=deduct['unit'])

                    # Deductions only can define use based discounts
                    if unit.defined_model != 'pay per use':
                        raise Exception('Invalid deduction')

                price_model['deductions'].append(deduct)

        # If not price components or all price components define a
        # function without currency, load default currency
        if 'general_currency' not in price_model:
            cnt = WStore_context.objects.all()[0]
            price_model['general_currency'] = cnt.allowed_currencies['default']

        # Calculate the revenue sharing class
        revenue_class = None
        if 'pay_per_use' in price_model:
            revenue_class = 'use'
        elif 'subscription' in price_model:
            revenue_class = 'subscription'
        elif 'single_payment' in price_model:
            revenue_class = 'single-payment'

        # Create the contract entry
        Contract.objects.create(
            pricing_model=price_model,
            charges=[],
            applied_sdrs=[],
            purchase=self._purchase,
            revenue_class=revenue_class
        )
        self._price_model = price_model

    def _calculate_renovation_date(self, unit):

        unit_model = Unit.objects.get(name=unit)

        now = datetime.now()
        # Transform now date into seconds
        now = time.mktime(now.timetuple())

        renovation_date = now + (unit_model.renovation_period * 86400)  # Seconds in a day

        renovation_date = datetime.fromtimestamp(renovation_date)
        return renovation_date

    def include_sdr(self, sdr):
        # Check the offering and customer
        off_data = sdr['offering']
        org = Organization.objects.get(name=off_data['organization'])
        offering = Offering.objects.get(name=off_data['name'], owner_organization=org, version=off_data['version'])

        if offering != self._purchase.offering:
            raise Exception('The offering defined in the SDR is not the purchase offering')

        customer = User.objects.get(username=sdr['customer'])

        if self._purchase.organization_owned:
            # Check if the user belongs to the organization
            profile = UserProfile.objects.get(user=customer)
            belongs = False

            for org in profile.organizations:
                if org['organization'] == self._purchase.owner_organization.pk:
                    belongs = True
                    break

            if not belongs:
                raise Exception('The user does not belongs to the owner organization')
        else:
            # Check if the user has purchased the offering
            if customer != self._purchase.customer:
                raise Exception('The user has not purchased the offering')

        # Extract the pricing model from the purchase
        self._price_model = self._purchase.contract.pricing_model

        if 'pay_per_use' not in self._price_model:
            raise Exception('No pay per use parts in the pricing model of the offering')

        # Check the correlation number and timestamp
        applied_sdrs = self._purchase.contract.applied_sdrs
        pending_sdrs = self._purchase.contract.pending_sdrs
        last_corr = 0
        last_time = 0

        if len(pending_sdrs) > 0:
            last_corr = int(pending_sdrs[-1]['correlation_number'])
            last_time = pending_sdrs[-1]['time_stamp']
            last_time = time.mktime(last_time.timetuple())
        else:
            if len(applied_sdrs) > 0:
                last_corr = int(applied_sdrs[-1]['correlation_number'])
                last_time = applied_sdrs[-1]['time_stamp']
                last_time = time.mktime(last_time.timetuple())

        try:
            time_stamp = datetime.strptime(sdr['time_stamp'], '%Y-%m-%dT%H:%M:%S.%f')
        except:
            time_stamp = datetime.strptime(sdr['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')

        time_stamp_sec = time.mktime(time_stamp.timetuple())

        if (int(sdr['correlation_number']) != last_corr + 1):
            raise Exception('Invalid correlation number, expected: ' + str(last_corr + 1))

        if last_time > time_stamp_sec:
            raise Exception('Invalid time stamp')

        # Check unit or component_label depending if the model defines components or
        # price functions
        found_model = False
        for comp in self._price_model['pay_per_use']:
            if 'price_function' not in comp:
                if sdr['unit'] == comp['unit']:
                    found_model = True
                    break
            else:
                for k, var in comp['price_function']['variables'].iteritems():
                    if var['type'] == 'usage' and var['label'] == sdr['component_label']:
                        found_model = True
                        break

        # Check if any deduction depends on the sdr variable
        found_deduction = False
        if 'deductions' in self._price_model:
            for comp in self._price_model['deductions']:
                if 'price_function' not in comp:
                    if sdr['unit'] == comp['unit']:
                        found_deduction = True
                        break
                else:
                    for k, var in comp['price_function']['variables'].iteritems():
                        if var['type'] == 'usage' and var['label'] == sdr['component_label']:
                            found_deduction = True
                            break

        if found_model or found_deduction:
            # Store the SDR
            sdr['time_stamp'] = time_stamp
            self._purchase.contract.pending_sdrs.append(sdr)
        else:
            raise Exception('The specified unit or component label is not included in the pricing model')

        self._purchase.contract.save()

    def _check_expenditure_limits(self, price):
        """
        Check if the user can purchase the offering depending on its
        expenditure limits and ir accumulated balance thought the RSS
        """
        # Check is an RSS instance is registered
        if not RSS.objects.all():
            return
        else:
            rss = RSS.objects.all()[0]

        actor = None
        # Check who is the charging actor (user or organization)
        actor = self._purchase.owner_organization

        # Check if the actor has defined expenditure limits
        if not actor.expenditure_limits:
            return

        charge = {
            'currency': self._price_model['general_currency'],
            'amount': price
        }

        # Check balance
        request_failure = None
        try:
            rss_factory = RSSManagerFactory(rss)
            exp_manager = rss_factory.get_expenditure_manager(rss.access_token)
            exp_manager.check_balance(charge, actor)
        except HTTPError as e:
            # Check if it is needed to refresh the access token
            if e.code == 401:
                rss._refresh_token()
                exp_manager.set_credentials(rss.access_token)
                try:
                    exp_manager.check_balance(charge, actor)
                # The user may be unauthorized, an error occurs, or the
                # actor balance is not enough
                except:
                    request_failure = e

            # Check if the error is due to an insufficient balance
            else:
                request_failure = e
        except:
            request_failure = e

        # Raise  the correct failure
        if request_failure:
            if type(request_failure) == HTTPError and request_failure.code == 404\
             and json.loads(request_failure.read())['exceptionId'] == 'SVC3705':
                    raise Exception('There is not enough balance. Check your expenditure limits')
            else:
                raise request_failure

        self._expenditure_used = True

    def _update_actor_balance(self, price):
        rss = RSS.objects.all()[0]

        actor = None
        # Check who is the charging actor (user or organization)
        if self._purchase.organization_owned:
            actor = self._purchase.owner_organization
        else:
            client = self._purchase.customer
            actor = Organization.objects.get(actor_id=client.userprofile.actor_id)

        charge = {
            'currency': self._price_model['general_currency'],
            'amount': price
        }

        # Check balance
        try:
            rss_factory = RSSManagerFactory(rss)
            exp_manager = rss_factory.get_expenditure_manager(rss.access_token)
            exp_manager.update_balance(charge, actor)
        except HTTPError as e:
            # Check if it is needed to refresh the access token
            if e.code == 401:
                rss._refresh_token()
                exp_manager.set_credentials(rss.access_token)
                exp_manager.update_balance(charge, actor)
            # Check if the error is due to an insufficient balance
            else:
                raise e

    def end_charging(self, price, concept, related_model, accounting=None):

        # Update purchase state
        if self._purchase.state == 'pending':
            self._purchase.state = 'paid'
            self._purchase.save()

        # Update contract
        contract = self._purchase.contract

        time_stamp = datetime.now()

        if price > 0:
            contract.charges.append({
                'date': time_stamp,
                'cost': price,
                'currency': contract.pricing_model['general_currency'],
                'concept': concept
            })

        contract.pending_payment = {}
        if self._price_model is None:
            self._price_model = contract.pricing_model

        contract.last_charge = time_stamp

        if concept == 'initial charge':
            # If a subscription part has been charged update renovation date
            if 'subscription' in related_model:
                updated_subscriptions = []

                for subs in self._price_model['subscription']:
                    up_sub = subs
                    # Calculate renovation date
                    up_sub['renovation_date'] = self._calculate_renovation_date(subs['unit'])
                    updated_subscriptions.append(up_sub)

                self._price_model['subscription'] = updated_subscriptions

                # Update price model in contract
                contract.pricing_model = self._price_model
                related_model['subscription'] = updated_subscriptions

            # Generate the invoice
            self._generate_invoice(price, related_model, 'initial')

        elif concept == 'Renovation':

            for subs in related_model['subscription']:
                subs['renovation_date'] = self._calculate_renovation_date(subs['unit'])

            updated_subscriptions = related_model['subscription']
            if 'unmodified' in related_model:
                updated_subscriptions.extend(related_model['unmodified'])

            self._price_model['subscription'] = updated_subscriptions
            contract.pricing_model = self._price_model
            related_model['subscription'] = updated_subscriptions

            if accounting:
                related_model['charges'] = accounting['charges']
                related_model['deductions'] = accounting['deductions']
                contract.applied_sdrs.extend(contract.pending_sdrs)
                contract.pending_sdrs = []

            self._generate_invoice(price, related_model, 'renovation')

        elif concept == 'pay per use':
            # Move SDR from pending to applied
            contract.applied_sdrs.extend(contract.pending_sdrs)
            contract.pending_sdrs = []
            # Generate the invoice
            self._generate_invoice(price, accounting, 'use')
            related_model['charges'] = accounting['charges']
            related_model['deductions'] = accounting['deductions']

        # The contract is saved before the CDR creation to prevent
        # that a transmission error in RSS request causes the
        # customer being charged twice
        contract.save()

        # If the customer has been charged create the CDR and update balance
        if price > 0:
            self._generate_cdr(related_model, str(time_stamp))
            if self._expenditure_used:
                self._update_actor_balance(price)

    def resolve_charging(self, new_purchase=False, sdr=False):

        # Check if there is a new purchase
        if new_purchase:
            # Create the contract
            self._create_purchase_contract()
            charge = False
            related_model = {}

            # Check if there are price parts different from pay per use
            if 'single_payment' in self._price_model:
                charge = True
                related_model['single_payment'] = self._price_model['single_payment']

            if 'subscription' in self._price_model:
                charge = True
                related_model['subscription'] = self._price_model['subscription']

            price = 0
            if charge:
                # Call the price resolver
                resolver = PriceResolver()
                price = resolver.resolve_price(related_model)

                # Check user expenditure limits and accumulated balance
                self._check_expenditure_limits(price)

                # Make the charge
                redirect_url = self._charge_client(price, 'initial charge', self._price_model['general_currency'])
            else:
                # If it is not necessary to charge the customer the state is set to paid
                self._purchase.state = 'paid'

            if self._purchase.state == 'paid':
                self.end_charging(price, 'initial charge', related_model)
            else:
                price = self._fix_price(price)
                self._purchase.contract.pending_payment = {
                    'price': price,
                    'concept': 'initial charge',
                    'related_model': related_model
                }
                self._purchase.contract.save()
                return redirect_url

        else:
            self._price_model = self._purchase.contract.pricing_model
            self._purchase.state = 'pending'
            self._purchase.save()

            # If not SDR received means that the call is a renovation
            if not sdr:
                # Determine the price parts to renovate
                if 'subscription' not in self._price_model:
                    raise Exception('No subscriptions to renovate')

                related_model = {
                    'subscription': []
                }

                now = datetime.now()
                unmodified = []

                for s in self._price_model['subscription']:
                    renovation_date = s['renovation_date']

                    if renovation_date < now:
                        related_model['subscription'].append(s)
                    else:
                        unmodified.append(s)

                accounting_info = None
                # If pending SDR documents resolve the use charging
                if len(self._purchase.contract.pending_sdrs) > 0:
                    related_model['pay_per_use'] = self._price_model['pay_per_use']
                    accounting_info = []
                    accounting_info.extend(self._purchase.contract.pending_sdrs)

                # If deductions have been included resolve the discount
                if 'deductions' in self._price_model and len(self._price_model['deductions']) > 0:
                    related_model['deductions'] = self._price_model['deductions']

                resolver = PriceResolver()
                price = resolver.resolve_price(related_model, accounting_info)

                # Deductions can make the price 0
                if price > 0:
                    # If not use made, check expenditure limits and accumulated balance
                    if not accounting_info:
                        self._check_expenditure_limits(price)

                    redirect_url = self._charge_client(price, 'Renovation', self._price_model['general_currency'])

                if len(unmodified) > 0:
                    related_model['unmodified'] = unmodified

                # Check if applied accounting info is needed to finish the purchase
                applied_accounting = None
                if accounting_info:
                    applied_accounting = resolver.get_applied_sdr()

                if self._purchase.state == 'paid':
                    self.end_charging(price, 'Renovation', related_model, applied_accounting)
                else:
                    price = self._fix_price(price)
                    pending_payment = {
                        'price': price,
                        'concept': 'Renovation',
                        'related_model': related_model
                    }

                    # If some accounting has been used include it to be saved
                    if accounting_info:
                        pending_payment['accounting'] = applied_accounting

                    self._purchase.contract.pending_payment
                    self._purchase.contract.save()
                    return redirect_url

            # If sdr is true means that the call is a request for charging the use
            # made of a service.
            else:
                # Aggregate the calculated charges
                pending_sdrs = []
                pending_sdrs.extend(self._purchase.contract.pending_sdrs)

                if len(pending_sdrs) == 0:
                    raise Exception('No SDRs to charge')

                related_model = {
                    'pay_per_use': self._price_model['pay_per_use']
                }

                if 'deductions' in self._price_model and len(self._price_model['deductions']) > 0:
                    related_model['deductions'] = self._price_model['deductions']

                resolver = PriceResolver()
                price = resolver.resolve_price(related_model, pending_sdrs)
                # Charge the client

                # Deductions can make the price 0
                if price > 0:
                    redirect_url = self._charge_client(price, 'Pay per use', self._price_model['general_currency'])

                applied_accounting = resolver.get_applied_sdr()

                if self._purchase.state == 'paid':
                    self.end_charging(price, 'pay per use', related_model, applied_accounting)
                else:
                    price = self._fix_price(price)
                    self._purchase.contract.pending_payment = {
                        'price': price,
                        'concept': 'pay per use',
                        'related_model': related_model,
                        'accounting': applied_accounting
                    }
                    self._purchase.contract.save()
                    return redirect_url
