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

from __future__ import absolute_import

import json
import time
import threading
from bson import ObjectId
from urllib2 import HTTPError
from datetime import datetime

from django.conf import settings

from wstore.models import Organization, Context as WStore_context
from wstore.models import Purchase
from wstore.models import RSS
from wstore.charging_engine.models import Contract
from wstore.charging_engine.models import Unit
from wstore.charging_engine.price_resolver import PriceResolver
from wstore.charging_engine.charging.cdr_manager import CDRManager
from wstore.charging_engine.invoice_builder import InvoiceBuilder
from wstore.contracting.purchase_rollback import rollback
from wstore.rss_adaptor.rss_manager_factory import RSSManagerFactory
from wstore.store_commons.database import get_database_connection


class ChargingEngine:

    _price_model = None
    _purchase = None
    _payment_method = None
    _plan = None
    _cdr_manager = None

    def __init__(self, purchase, payment_method=None, plan=None, credit_card=None):
        self._purchase = purchase
        if payment_method is not None:

            if payment_method != 'paypal':
                if credit_card is None:
                    raise Exception('Invalid payment method')

            self._payment_method = payment_method

        if plan:
            self._plan = plan

        if credit_card is not None:
            self._credit_card_info = credit_card

        self._expenditure_used = False
        self._cdr_manager = CDRManager(self._purchase)

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
                price += '0'

        return price

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
            self._purchase.save()

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
                self._purchase.save()
        else:
            raise Exception('Invalid payment method')

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
        except Exception as e:
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

        invoice_builder = InvoiceBuilder(self._purchase)

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
            invoice_builder.generate_invoice(price, related_model, 'initial')

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

            invoice_builder.generate_invoice(price, related_model, 'renovation')

        elif concept == 'pay per use':
            # Move SDR from pending to applied
            contract.applied_sdrs.extend(contract.pending_sdrs)
            contract.pending_sdrs = []
            # Generate the invoice
            invoice_builder.generate_invoice(price, accounting, 'use')
            related_model['charges'] = accounting['charges']
            related_model['deductions'] = accounting['deductions']

        # The contract is saved before the CDR creation to prevent
        # that a transmission error in RSS request causes the
        # customer being charged twice
        contract.save()
        self._purchase.save()

        # If the customer has been charged create the CDR and update balance
        if price > 0:
            self._cdr_manager.generate_cdr(related_model, str(time_stamp))
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
