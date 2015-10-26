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
from __future__ import unicode_literals

import time
import threading
from bson import ObjectId
from datetime import datetime

from django.conf import settings

from wstore.models import Purchase, Context
from wstore.charging_engine.models import Contract
from wstore.charging_engine.models import Unit
from wstore.charging_engine.price_resolver import PriceResolver
from wstore.charging_engine.charging.cdr_manager import CDRManager
from wstore.charging_engine.charging.balance_manager import BalanceManager
from wstore.charging_engine.invoice_builder import InvoiceBuilder
from wstore.contracting.purchase_rollback import rollback
from wstore.store_commons.database import get_database_connection


class ChargingEngine:

    def __init__(self, purchase, payment_method=None, plan=None, credit_card=None):
        self._purchase = purchase
        if payment_method is not None:

            if payment_method != 'paypal':
                if credit_card is None:
                    raise Exception('Invalid payment method')

            self._payment_method = payment_method

        self._plan = None
        if plan:
            self._plan = plan

        if credit_card is not None:
            self._credit_card_info = credit_card

        self._expenditure_used = False
        self._cdr_manager = CDRManager(self._purchase)
        self._balance_manager = BalanceManager(self._purchase)
        self._price_resolver = PriceResolver()
        self._concept = None
        self._price_model = None

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

    def _charge_client(self, price):

        # Load payment client
        cln_str = settings.PAYMENT_CLIENT
        client_class = cln_str.split('.')[-1]
        client_package = cln_str.partition('.' + client_class)[0]

        payment_client = getattr(__import__(client_package, globals(), locals(), [client_class], -1), client_class)

        # build the payment client
        client = payment_client(self._purchase)
        price = self._fix_price(price)

        if self._payment_method == 'credit_card':
            client.direct_payment(self._price_model['general_currency'], price, self._credit_card_info)
            self._purchase.state = 'paid'
            self._purchase.save()

        elif self._payment_method == 'paypal':
            client.start_redirection_payment(price, self._price_model['general_currency'])

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

    def _calculate_renovation_date(self, unit):

        unit_model = Unit.objects.get(name=unit)

        now = datetime.now()
        # Transform now date into seconds
        now = time.mktime(now.timetuple())

        renovation_date = now + (unit_model.renovation_period * 86400)  # Seconds in a day

        renovation_date = datetime.fromtimestamp(renovation_date)
        return renovation_date

    def _end_initial_charge(self, related_model, accounting=None):
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
            self._purchase.contract.pricing_model = self._price_model
            related_model['subscription'] = updated_subscriptions

    def _end_renovation_charge(self, related_model, accounting=None):
        for subs in related_model['subscription']:
            subs['renovation_date'] = self._calculate_renovation_date(subs['unit'])

        updated_subscriptions = related_model['subscription']
        if 'unmodified' in related_model:
            updated_subscriptions.extend(related_model['unmodified'])

        self._price_model['subscription'] = updated_subscriptions
        self._purchase.contract.pricing_model = self._price_model
        related_model['subscription'] = updated_subscriptions

        if accounting:
            self._end_use_charge(related_model, accounting)

    def _end_use_charge(self, related_model, accounting=None):
        # Move SDR from pending to applied
        self._purchase.contract.applied_sdrs.extend(self._purchase.contract.pending_sdrs)
        self._purchase.contract.pending_sdrs = []
        related_model['charges'] = accounting['charges']
        related_model['deductions'] = accounting['deductions']

    def end_charging(self, price, concept, related_model, accounting=None):
        """
        Process the second step of a payment once the customer has approved the charge
        :param price: Total price charged
        :param concept: Concept of the charge, it can be initial, renovation, or use
        :param related_model: Pricing model that has been applied including
        :param accounting: Accounting information used to compute the charged for pay-per-use models
        """

        end_processors = {
            'initial': self._end_initial_charge,
            'renovation': self._end_renovation_charge,
            'use': self._end_use_charge
        }

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

        end_processors[concept](related_model, accounting)

        # Generate the invoice
        invoice_builder = InvoiceBuilder(self._purchase)
        invoice_builder.generate_invoice(price, related_model, concept)

        # The contract is saved before the CDR creation to prevent
        # that a transmission error in RSS request causes the
        # customer being charged twice
        contract.save()
        self._purchase.save()

        # If the customer has been charged create the CDR and update balance
        if price > 0:
            self._cdr_manager.generate_cdr(related_model, str(time_stamp))
            if self._balance_manager.has_limits():
                self._balance_manager.update_actor_balance(price)

    def _get_effective_pricing(self, parsed_usdl):
        # Search and validate the corresponding price plan
        usdl_pricing = {}
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
                        break

                # Validate the specified plan
                if not found:
                    raise Exception('The specified plan does not exist')

        return usdl_pricing

    def _get_default_currency(self):
        cnt = Context.objects.all()[0]
        return cnt.allowed_currencies['default']

    def _create_purchase_contract(self):
        # Generate the pricing model structure

        usdl_pricing = self._get_effective_pricing(self._purchase.offering.offering_description)

        if 'currency' not in usdl_pricing:
            currency = self._get_default_currency()
        else:
            currency = usdl_pricing['currency']

        price_model = {
            'general_currency': currency
        }
        if self._plan is not None:
            price_model['label'] = self._plan

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

    def _save_pending_charge(self, price, related_model, applied_accounting=None):
        price = self._fix_price(price)
        pending_payment = {
            'price': price,
            'concept': self._concept,
            'related_model': related_model
        }

        # If some accounting has been used include it to be saved
        if applied_accounting:
            pending_payment['accounting'] = applied_accounting

        self._purchase.contract.pending_payment = pending_payment
        self._purchase.contract.save()

    def _process_initial_charge(self):
        """
        Resolves initial charges, which can include single payments or the initial payment of a subscription
        :return: The URL where redirecting the customer to approve the charge
        """
        # Create the contract
        self._create_purchase_contract()

        related_model = {}
        redirect_url = None

        # Check if there are price parts different from pay per use
        if 'single_payment' in self._price_model:
            related_model['single_payment'] = self._price_model['single_payment']

        if 'subscription' in self._price_model:
            related_model['subscription'] = self._price_model['subscription']

        price = 0
        if len(related_model):
            # Call the price resolver
            price = self._price_resolver.resolve_price(related_model)

            # Check user expenditure limits and accumulated balance
            self._balance_manager.check_expenditure_limits(price)

            # Make the charge
            redirect_url = self._charge_client(price)
        else:
            # If it is not necessary to charge the customer the state is set to paid
            self._purchase.state = 'paid'

        if self._purchase.state == 'paid':
            self.end_charging(price, self._concept, related_model)
        else:
            self._save_pending_charge(price, related_model)

        return redirect_url

    def _extract_model(self):
        self._price_model = self._purchase.contract.pricing_model
        self._purchase.state = 'pending'
        self._purchase.save()

    def _process_usage(self, related_model, unmodified=None):

        redirect_url = None
        accounting_info = None

        # If pending SDR documents resolve the use charging
        if len(self._purchase.contract.pending_sdrs) > 0:
            related_model['pay_per_use'] = self._price_model['pay_per_use']
            accounting_info = []
            accounting_info.extend(self._purchase.contract.pending_sdrs)

        # If deductions have been included resolve the discount
        if 'deductions' in self._price_model and len(self._price_model['deductions']) > 0:
            related_model['deductions'] = self._price_model['deductions']

        price = self._price_resolver.resolve_price(related_model, accounting_info)

        # Check if applied accounting info is needed to finish the purchase
        applied_accounting = None
        if accounting_info is not None:
            applied_accounting = self._price_resolver.get_applied_sdr()

        # Deductions can make the price 0
        if price > 0:
            # If not use made, check expenditure limits and accumulated balance
            if applied_accounting is None:
                self._balance_manager.check_expenditure_limits(price)

            redirect_url = self._charge_client(price)

        if unmodified is not None and len(unmodified) > 0:
            related_model['unmodified'] = unmodified

        if self._purchase.state == 'paid':
            self.end_charging(price, self._concept, related_model, applied_accounting)
        else:
            self._save_pending_charge(price, related_model, applied_accounting=applied_accounting)

        return price, applied_accounting, redirect_url

    def _process_renovation_charge(self):
        """
        Resolves renovation charges, which includes the renovation of subscriptions and optionally usage payments
        :return: The URL where redirecting the customer to approve the charge
        """
        self._extract_model()

        # Determine the price parts to renovate
        if 'subscription' not in self._price_model:
            raise ValueError('The pricing model does not contain any subscription to renovate')

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

        price, applied_accounting, redirect_url = self._process_usage(related_model, unmodified=unmodified)

        return redirect_url

    def _process_use_charge(self):
        """
        Resolves usage charges, which includes pay-per-use payments
        :return: The URL where redirecting the customer to approve the charge
        """
        self._extract_model()

        if not len(self._purchase.contract.pending_sdrs):
            raise ValueError('There is not pending SDRs to process')

        related_model = {}
        price, applied_accounting, redirect_url = self._process_usage(related_model)

        return redirect_url

    def resolve_charging(self, type_='initial'):
        """
        Calculates the charge of a customer depending on the pricing model and the type of charge.
        :param type_: Type of charge, it defines if it is an initial charge, a renovation or a usage based charge
        :return: The URL where redirecting the user to be charged (PayPal)
        """

        self._concept = type_

        charging_processors = {
            'initial': self._process_initial_charge,
            'renovation': self._process_renovation_charge,
            'use': self._process_use_charge
        }

        if type_ not in charging_processors:
            raise ValueError('Invalid charge type, must be initial, renovation, or use')

        return charging_processors[type_]()
