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
from copy import deepcopy
from datetime import datetime
from bson import ObjectId
from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.contrib.auth.models import User

from wstore.charging_engine import charging_engine
from wstore.charging_engine import views
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.models import Organization
from wstore.charging_engine.management.commands import resolve_use_charging
from wstore.store_commons.database import get_database_connection


__test__ = False


def fake_renovation_date(unit):

    if unit == 'per month':
        return datetime(2013, 04, 01, 00, 00, 00)
    elif unit == 'per week':
        return datetime(2013, 03, 20, 00, 00, 00)


class FakeClient():

    def __init__(self, purchase):
        pass

    def start_redirection_payment(self, price, currency):
        pass

    def end_redirection_payment(self, token, payer_id):
        pass

    def direct_payment(self, currency, price, credit_card):
        pass

    def get_checkout_url(self):
        return 'https://www.sandbox.paypal.com/webscr?cmd=_express-checkout&token=11111111'


class FakeThreading():

    class Timer():

        def __init__(self, time, handler):
            pass

        def start(self):
            pass


class FakeChargingEngine():

    _purchase = None
    _payment_method = None
    _credit_card = None

    def __init__(self, purchase, payment_method, credit_card):
        self._purchase = purchase
        self._payment_method = payment_method
        self._credit_card = credit_card

    def resolve_charging(self, sdr=False):

        if sdr and self._payment_method == 'credit_card':
            sdrs = self._purchase.contract.pending_sdrs
            self._purchase.contract.pending_sdrs = []
            self._purchase.contract.applied_sdrs.extend(sdrs)
            self._purchase.contract.save()


def fake_cdr_generation(parts, time):
    pass


class FakeSubprocess():

    def __init__(self):
        pass

    def call(self, prams):
        pass

BASIC_PRCING = {
    "pricing": {
        "price_plans": [{
            "currency": "EUR",
            "title": "Example price plan",
            "description": "Price plan description",
            "price_components": [{
                "label": "Price component 1",
                "unit": "single payment",
                "value": "5",
                "description": "price component 1 description"
            }]
        }]
    }
}


MULTIPLE_PRCING = {
    "pricing": {
        "price_plans": [{
            "currency": "EUR",
            "title": "Example price plan",
            "description": "Price plan description",
            "price_components": [{
                "label": "Price component 1",
                "unit": "single payment",
                "value": "5",
                "description": "price component 1 description"
            }, {
                "label": "Price component 2",
                "unit": "single payment",
                "value": "5",
                "description": "price component 2 description"
            }, {
                "label": "Price component 3",
                "unit": "single payment",
                "value": "7",
                "description": "price component 3 description"
            }]
        }]
    }
}


class SinglePaymentChargingTestCase(TestCase):

    tags = ('fiware-ut-12',)
    fixtures = ['single_payment.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        reload(charging_engine)
        cls._auth = settings.OILAUTH
        charging_engine.subprocess = FakeSubprocess()
        settings.OILAUTH = False
        settings.PAYMENT_CLIENT = 'wstore.charging_engine.tests.FakeClient'
        super(SinglePaymentChargingTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        settings.OILAUTH = cls._auth
        super(SinglePaymentChargingTestCase, cls).tearDownClass()

    def setUp(self):
        charging_engine.CDRManager = MagicMock()

    @parameterized.expand([
        ('basic',  BASIC_PRCING, 5),
        ('multiple', MULTIPLE_PRCING, 17)
    ])
    def test_charging_single_payment(self, name, pricing_model, value):
        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        purchase.offering.offering_description = pricing_model
        purchase.offering.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)

        charging._generate_cdr = fake_cdr_generation
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.resolve_charging(new_purchase=True)

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        bills = purchase.bill

        self.assertEqual(len(bills), 1)

        contract = purchase.contract
        charges = contract.charges

        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0]['cost'], value)
        self.assertEqual(charges[0]['currency'], 'EUR')
        self.assertEqual(charges[0]['concept'], 'initial charge')

        price_model = contract.pricing_model

        self.assertTrue('single_payment' in price_model)
        self.assertFalse('subscription' in price_model)
        self.assertFalse('pay_per_use' in price_model)

        self.assertEqual(len(price_model['single_payment']), len(pricing_model['pricing']['price_plans'][0]['price_components']))

        for pay in price_model['single_payment']:
            if pay['label'] == 'Price component 1':
                self.assertEqual(pay['value'], '5')

            elif pay['label'] == 'Price component 2':
                self.assertEqual(pay['value'], '5')

            elif pay['label'] == 'Price component 3':
                self.assertEqual(pay['value'], '7')


class SubscriptionChargingTestCase(TestCase):

    tags = ('fiware-ut-13',)
    fixtures = ['subscription.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        settings.PAYMENT_CLIENT = 'wstore.charging_engine.tests.FakeClient'
        charging_engine.subprocess = FakeSubprocess()
        super(SubscriptionChargingTestCase, cls).setUpClass()

    def test_basic_subscription_charging(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging_engine.CDRManager = MagicMock()

        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging._calculate_renovation_date = fake_renovation_date
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.resolve_charging(new_purchase=True)
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['cost'], 10)
        self.assertEqual(contract.charges[0]['currency'], 'EUR')
        self.assertEqual(contract.charges[0]['concept'], 'initial charge')

        pricing_model = contract.pricing_model

        self.assertTrue('subscription' in pricing_model)
        self.assertFalse('single_payment' in pricing_model)
        self.assertFalse('pay_per_use' in pricing_model)

        for sub in pricing_model['subscription']:
            if sub['label'] == 'Price component 1':
                self.assertEqual(sub['value'], '5.0')
                self.assertEqual(sub['unit'], 'per month')
                self.assertEqual(str(sub['renovation_date']), '2013-04-01 00:00:00')
            else:
                self.assertEqual(sub['label'], 'Price component 2')
                self.assertEqual(sub['value'], '5.0')
                self.assertEqual(sub['unit'], 'per week')
                self.assertEqual(str(sub['renovation_date']), '2013-03-20 00:00:00')

    def test_basic_renovation_charging(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk="61005a1a8205ac3115111111")
        contract = purchase.contract

        # Change renovation date type (JSON does not allow complex types as MongoDB does)
        new_subs = []
        for sub in contract.pricing_model['subscription']:

            new_sub = sub
            new_sub['renovation_date'] = datetime.strptime(new_sub['renovation_date'], '%Y-%m-%d %H:%M:%S')
            new_subs.append(new_sub)

        contract.pricing_model['subscription'] = new_subs
        contract.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging._calculate_renovation_date = fake_renovation_date

        charging._generate_cdr = fake_cdr_generation
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.resolve_charging()
        purchase = Purchase.objects.get(pk="61005a1a8205ac3115111111")
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 2)
        self.assertEqual(contract.charges[0]['cost'], 10)
        self.assertEqual(contract.charges[0]['currency'], 'EUR')
        self.assertEqual(contract.charges[0]['concept'], 'initial')
        self.assertEqual(contract.charges[1]['cost'], 10)
        self.assertEqual(contract.charges[1]['currency'], 'EUR')
        self.assertEqual(contract.charges[1]['concept'], 'Renovation')

        pricing_model = contract.pricing_model

        self.assertTrue('subscription' in pricing_model)
        self.assertFalse('single_payment' in pricing_model)
        self.assertFalse('pay_per_use' in pricing_model)

        for sub in pricing_model['subscription']:
            if sub['label'] == 'price component 1':
                self.assertEqual(sub['value'], '5')
                self.assertEqual(sub['unit'], 'per month')
                self.assertEqual(str(sub['renovation_date']), '2013-04-01 00:00:00')
            else:
                self.assertEqual(sub['label'], 'price component 2')
                self.assertEqual(sub['value'], '5')
                self.assertEqual(sub['unit'], 'per week')
                self.assertEqual(str(sub['renovation_date']), '2013-03-20 00:00:00')

    def test_partial_renovation(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e06ac2015f022f0')
        contract = purchase.contract

        # Change renovation date type (JSON does not allow complex types as MongoDB does)
        new_subs = []
        for sub in contract.pricing_model['subscription']:

            new_sub = sub
            new_sub['renovation_date'] = datetime.strptime(new_sub['renovation_date'], '%Y-%m-%d %H:%M:%S')
            new_subs.append(new_sub)

        contract.pricing_model['subscription'] = new_subs
        contract.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging._calculate_renovation_date = fake_renovation_date

        charging._generate_cdr = fake_cdr_generation
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.resolve_charging()
        purchase = Purchase.objects.get(pk='61005aba8e06ac2015f022f0')
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 2)
        self.assertEqual(contract.charges[0]['cost'], 10)
        self.assertEqual(contract.charges[0]['currency'], 'EUR')
        self.assertEqual(contract.charges[0]['concept'], 'initial')
        self.assertEqual(contract.charges[1]['cost'], 5)
        self.assertEqual(contract.charges[1]['currency'], 'EUR')
        self.assertEqual(contract.charges[1]['concept'], 'Renovation')

        pricing_model = contract.pricing_model

        self.assertTrue('subscription' in pricing_model)
        self.assertFalse('single_payment' in pricing_model)
        self.assertFalse('pay_per_use' in pricing_model)

        for s in pricing_model['subscription']:
            if s['label'] == 'price component 1':
                self.assertEqual(s['value'], '5')
                self.assertEqual(s['unit'], 'per month')
                self.assertEqual(str(s['renovation_date']), '2013-04-01 00:00:00')
            else:
                self.assertEqual(s['value'], '5')
                self.assertEqual(s['unit'], 'per week')
                self.assertEqual(str(s['renovation_date']), '2020-04-01 00:00:00')

    def test_renovation_no_subscription(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk="61015a1a1e06ac2015f122f0")
        charging = charging_engine.ChargingEngine(purchase)

        error = False
        try:
            charging.resolve_charging()
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'No subscriptions to renovate')


class PayPerUseChargingTestCase(TestCase):

    fixtures = ['payperuse.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        cls._auth = settings.OILAUTH
        settings.PAYMENT_CLIENT = 'wstore.charging_engine.tests.FakeClient'
        charging_engine.subprocess = FakeSubprocess()
        settings.OILAUTH = False
        super(PayPerUseChargingTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        settings.OILAUTH = cls._auth
        super(PayPerUseChargingTestCase, cls).tearDownClass()

    def test_new_purchase_use(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61074ab65e05acc415f77777')

        charging_engine.CDRManager = MagicMock()

        charging = charging_engine.ChargingEngine(purchase)
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.resolve_charging(new_purchase=True)

        purchase = Purchase.objects.get(pk='61074ab65e05acc415f77777')

        bills = purchase.bill
        self.assertEqual(len(bills), 1)

        self.assertEqual(purchase.state, 'paid')
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 0)
        price_model = contract.pricing_model

        self.assertFalse('single_payment' in price_model)
        self.assertFalse('subscription' in price_model)
        self.assertTrue('pay_per_use' in price_model)

        self.assertEqual(len(price_model['pay_per_use']), 1)
        self.assertEqual(price_model['pay_per_use'][0]['label'], 'Pay per use')
        self.assertEqual(price_model['pay_per_use'][0]['value'], '5.0')
        self.assertEqual(price_model['pay_per_use'][0]['unit'], 'invocation')
        self.assertEqual(price_model['general_currency'], 'EUR')

    test_new_purchase_use.tags = ('fiware-ut-16',)

    def test_basic_resolve_use_charging(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61077ab75e07a7c415f372f2')
        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)

        charging.CDRGeneration = MagicMock()
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.resolve_charging(sdr=True)

        purchase = Purchase.objects.get(pk='61077ab75e07a7c415f372f2')

        bills = purchase.bill
        self.assertEqual(len(bills), 1)

        self.assertEqual(purchase.state, 'paid')

        contract = purchase.contract

        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['cost'], 10.00)
        self.assertEqual(contract.charges[0]['concept'], 'pay per use')

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 1)

    test_basic_resolve_use_charging.tags = ('fiware-ut-15',)

    def test_resolve_use_charging_no_sdr(self):

        purchase = Purchase.objects.get(pk='61004a9a5e95ac9115902290')
        charging = charging_engine.ChargingEngine(purchase)

        error = False
        msg = None
        try:
            charging.resolve_charging(sdr=True)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEquals(msg, 'No SDRs to charge')

    test_resolve_use_charging_no_sdr.tags = ('fiware-ut-15',)


class AsynchronousPaymentTestCase(TestCase):

    tags = ('fiware-ut-17',)
    fixtures = ['async.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        settings.PAYMENT_CLIENT = 'wstore.charging_engine.tests.FakeClient'
        charging_engine.subprocess = FakeSubprocess()
        charging_engine.threading = FakeThreading()
        super(AsynchronousPaymentTestCase, cls).setUpClass()

    def setUp(self):
        charging_engine.CDRManager = MagicMock()

    def test_basic_asynchronous_payment(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        # First step
        charging = charging_engine.ChargingEngine(purchase, payment_method='paypal')
        url = charging.resolve_charging(new_purchase=True)

        self.assertEqual(url, 'https://www.sandbox.paypal.com/webscr?cmd=_express-checkout&token=11111111')
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        self.assertEqual(purchase.state, 'pending')
        self.assertEqual(len(purchase.bill), 0)

        contract = purchase.contract
        self.assertEqual(len(contract.charges), 0)
        self.assertEqual(contract.pending_payment['price'], '5.00')
        self.assertEqual(contract.pending_payment['concept'], 'initial charge')

        model = contract.pending_payment['related_model']
        self.assertEqual(len(model['single_payment']), 1)
        self.assertEqual(model['single_payment'][0]['label'], 'Price component 1')
        self.assertEqual(model['single_payment'][0]['value'], '5')

        # Second step
        charging = charging_engine.ChargingEngine(purchase)
        charging._check_expenditure_limits = MagicMock()
        charging._update_actor_balance = MagicMock()
        charging.end_charging(contract.pending_payment['price'], contract.pending_payment['concept'], contract.pending_payment['related_model'])

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        self.assertEqual(purchase.state, 'paid')
        bills = purchase.bill

        self.assertEqual(len(bills), 1)

        contract = purchase.contract
        self.assertEqual(len(contract.charges), 1)

        self.assertEqual(contract.charges[0]['cost'], '5.00')
        self.assertEqual(contract.charges[0]['currency'], 'EUR')
        self.assertEqual(contract.charges[0]['concept'], 'initial charge')

        self.assertEqual(contract.pending_payment, {})

    def test_timeout(self):

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        charging = charging_engine.ChargingEngine(purchase)

        def fakeroll(purch):
            purch.state = 'rollback'
            purch.save()

        charging_engine.rollback = fakeroll
        charging._timeout_handler()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        self.assertEqual(purchase.state, 'rollback')

    def test_timeout_locked(self):
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f02111')
        charging = charging_engine.ChargingEngine(purchase)

        db = get_database_connection()

        raw_purchase = db.wstore_purchase.find_one({'_id': ObjectId(purchase.pk)})
        raw_purchase['_lock'] = True

        db.wstore_purchase.save(raw_purchase)

        def fakeroll(purch):
            purch.state = 'rollback'
            purch.save()

        charging_engine.rollback = fakeroll
        charging._timeout_handler()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f02111')
        self.assertEqual(purchase.state, 'pending')

    def test_timeout_finished(self):
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f02222')
        charging = charging_engine.ChargingEngine(purchase)

        db = get_database_connection()

        raw_purchase = db.wstore_purchase.find_one({'_id': ObjectId(purchase.pk)})
        raw_purchase['_lock'] = False

        db.wstore_purchase.save(raw_purchase)

        def fakeroll(purch):
            purch.state = 'rollback'
            purch.save()

        charging_engine.rollback = fakeroll
        charging._timeout_handler()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f02222')
        self.assertEqual(purchase.state, 'paid')


class ChargingDaemonTestCase(TestCase):

    tags = ('fiware-ut-15',)
    fixtures = ['use_daemon.json']
    _command = None

    @classmethod
    def setUpClass(cls):

        resolve_use_charging.ChargingEngine = FakeChargingEngine
        cls._command = resolve_use_charging.Command()
        super(ChargingDaemonTestCase, cls).setUpClass()

    def test_basic_charging_daemon(self):

        # Fill userprofile model
        user = User.objects.get(pk='51000aba8e05ac2115f022f9')
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')

        user.userprofile.organization = org
        user.userprofile.payment_info = {
        }

        user.userprofile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        # Add dateinfo to sdr
        pending_sdrs = []
        pending_sdrs.append({
            'time_stamp': datetime(2013, 04, 01, 00, 00, 00, 00)
        })

        purchase.contract.pending_sdrs = pending_sdrs

        purchase.contract.save()

        # Run the method
        self._command.handle()

        # Check the contract
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        contract = purchase.contract

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 1)

    def test_charging_daemon_multiple_sdrs(self):

        # Fill userprofile model
        user = User.objects.get(pk='51000aba8e05ac2115f022f9')
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')

        user.userprofile.organization = org
        user.userprofile.payment_info = {
        }

        user.userprofile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        # Add dateinfo to sdr
        pending_sdrs = []
        pending_sdrs.append({
            'time_stamp': datetime(2013, 04, 01, 00, 00, 00, 00)
        })
        pending_sdrs.append({
            'time_stamp': datetime(2013, 04, 02, 00, 00, 00, 00)
        })
        pending_sdrs.append({
            'time_stamp': datetime(2013, 04, 03, 00, 00, 00, 00)
        })

        purchase.contract.pending_sdrs = pending_sdrs

        purchase.contract.save()

        # Run the method
        self._command.handle()

        # Check the contract
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        contract = purchase.contract

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 3)

    def test_charging_daemon_multiple_contracts(self):

        # Fill userprofile model
        user = User.objects.get(pk='51000aba8e05ac2115f022f9')
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')

        user.userprofile.organization = org
        user.userprofile.payment_info = {
        }

        user.userprofile.save()

        purchase_1 = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        purchase_2 = Purchase.objects.get(pk='61004aba5e05acc115f03333')

        # Add dateinfo to sdr
        pending_sdrs_1 = []
        pending_sdrs_1.append({
            'time_stamp': datetime(2013, 04, 01, 00, 00, 00, 00)
        })

        pending_sdrs_2 = []
        pending_sdrs_2.append({
            'time_stamp': datetime(2013, 04, 01, 00, 00, 00, 00)
        })
        pending_sdrs_2.append({
            'time_stamp': datetime(2013, 04, 02, 00, 00, 00, 00)
        })
        pending_sdrs_2.append({
            'time_stamp': datetime(2013, 04, 03, 00, 00, 00, 00)
        })

        purchase_1.contract.pending_sdrs = pending_sdrs_1
        purchase_1.contract.save()

        purchase_2.contract.pending_sdrs = pending_sdrs_2
        purchase_2.contract.save()

        # Run the method
        self._command.handle()

        # Check the first contract
        purchase_1 = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        contract = purchase_1.contract

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 1)

        # Check the first contract
        purchase_2 = Purchase.objects.get(pk='61004aba5e05acc115f03333')

        contract = purchase_2.contract

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 3)

    def test_charging_daemon_organization_purchased(self):

        # Fill userprofile model
        user = User.objects.get(pk='51000aba8e05ac2115f022f9')
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')

        org.payment_info = {}
        org.save()

        user.userprofile.organization = org

        user.userprofile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f08888')

        # Add dateinfo to sdr
        pending_sdrs = []
        pending_sdrs.append({
            'time_stamp': datetime(2013, 04, 01, 00, 00, 00, 00)
        })

        purchase.contract.pending_sdrs = pending_sdrs

        purchase.contract.save()

        # Run the method
        self._command.handle()

        # Check the contract
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f08888')

        contract = purchase.contract

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 1)

    def test_charging_daemon_now_time(self):

        # Fill userprofile model
        user = User.objects.get(pk='51000aba8e05ac2115f022f9')
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')

        user.userprofile.organization = org
        user.userprofile.payment_info = {
        }

        user.userprofile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        # Add dateinfo to sdr
        pending_sdrs = []
        pending_sdrs.append({
            'time_stamp': datetime.now()
        })

        purchase.contract.pending_sdrs = pending_sdrs

        purchase.contract.save()

        # Run the method
        self._command.handle()

        # Check the contract
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        contract = purchase.contract

        self.assertEqual(len(contract.pending_sdrs), 1)
        self.assertEqual(len(contract.applied_sdrs), 0)


class PriceFunctionPaymentTestCase(TestCase):

    fixtures = ['price_function.json']
    tags = ('fiware-ut-27',)

    @classmethod
    def setUpClass(cls):
        cls._auth = settings.OILAUTH
        settings.PAYMENT_CLIENT = 'wstore.charging_engine.tests.FakeClient'
        charging_engine.subprocess = FakeSubprocess()
        settings.OILAUTH = False
        super(PriceFunctionPaymentTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        settings.OILAUTH = cls._auth
        super(PriceFunctionPaymentTestCase, cls).tearDownClass()

    def test_basic_price_function_payment(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = user.userprofile

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging_engine.CDRManager = MagicMock()
        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging.resolve_charging(sdr=True)

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        bills = purchase.bill
        self.assertEqual(len(bills), 1)

        self.assertEqual(purchase.state, 'paid')

        contract = purchase.contract

        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['cost'], 33.00)
        self.assertEqual(contract.charges[0]['concept'], 'pay per use')

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 3)

    def test_price_function_payment_renovation(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = user.userprofile

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f55555')
        contract = purchase.contract

        # Change renovation date type (JSON does not allow complex types as MongoDB does)
        new_sub = contract.pricing_model['subscription'][0]

        new_sub['renovation_date'] = datetime.strptime(new_sub['renovation_date'], '%Y-%m-%d %H:%M:%S')

        contract.pricing_model['subscription'] = [new_sub]
        contract.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging_engine.CDRManager = MagicMock()
        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging._calculate_renovation_date = fake_renovation_date
        charging.resolve_charging()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f55555')

        bills = purchase.bill
        self.assertEqual(len(bills), 1)

        self.assertEqual(purchase.state, 'paid')

        contract = purchase.contract

        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['cost'], 38.00)
        self.assertEqual(contract.charges[0]['concept'], 'Renovation')

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 3)


    def test_price_function_payment_deduction(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = user.userprofile

        tax_address = {
            "street": "test street",
            "postal": "20000",
            "city": "test city",
            "country": "test country"
        }

        profile.tax_address = tax_address
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f77777')
        contract = purchase.contract

        # Change renovation date type (JSON does not allow complex types as MongoDB does)
        new_sub = contract.pricing_model['subscription'][0]

        new_sub['renovation_date'] = datetime.strptime(new_sub['renovation_date'], '%Y-%m-%d %H:%M:%S')

        contract.pricing_model['subscription'] = [new_sub]
        contract.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging_engine.CDRManager = MagicMock()
        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging._calculate_renovation_date = fake_renovation_date
        charging.resolve_charging()

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f77777')

        bills = purchase.bill
        self.assertEqual(len(bills), 1)

        self.assertEqual(purchase.state, 'paid')

        contract = purchase.contract

        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['cost'], 33.30)
        self.assertEqual(contract.charges[0]['concept'], 'Renovation')

        self.assertEqual(len(contract.pending_sdrs), 0)
        self.assertEqual(len(contract.applied_sdrs), 3)

    def test_price_function_payment_exception(self):

        from wstore.charging_engine.price_resolver import PriceResolver

        resolver = PriceResolver()

        # Load testing info
        errors = {
            'Invalid argument 1': {
                'arg1': 8,
                'arg2': 'arg',
                'operation': '*'
            },
            'Invalid argument 2': {
                'arg1': 'arg',
                'arg2': 6,
                'operation': '*'
            },
            'Unsupported operation': {
                'arg1': 'arg',
                'arg2': 'arg',
                'operation': 'p'
            }
        }

        var = {
            'arg': '3'
        }
        # Check possible exceptions
        for err, info in errors.iteritems():
            error = False
            msg = None
            try:
                resolver._price_function_calculation(info, var)
            except Exception, e:
                error = True
                msg = e.message

            self.assertTrue(error)
            self.assertEquals(msg, err)


SDR_INT1 = {
    u'component_label': u'usage',
    u'correlation_number': 1,
    u'customer': u'test_user',
    u'offering': {
        u'name': u'PayPerUse',
        u'organization': u'fdelavega',
        u'version': u'1.0'
    },
    u'record_type': u'event',
    u'time_stamp': datetime(2015, 9, 14, 10, 0),
    u'unit': u'invocation',
    u'value': 100
}

SDR_INT2 = {
    u'component_label': u'usage',
    u'correlation_number': 2,
    u'customer': u'test_user',
    u'offering': {
        u'name': u'PayPerUse',
        u'organization': u'fdelavega',
        u'version': u'1.0'
    },
    u'record_type': u'event',
    u'time_stamp': datetime(2015, 9, 14, 10, 0, 1),
    u'unit': u'invocation',
    u'value': 100
}

SDR_INT3 = {
    u'component_label': u'usage',
    u'correlation_number': 3,
    u'customer': u'test_user',
    u'offering': {
        u'name': u'PayPerUse',
        u'organization': u'fdelavega',
        u'version': u'1.0'
    },
    u'record_type': u'event',
    u'time_stamp': datetime(2015, 9, 14, 10, 0, 2),
    u'unit': u'invocation',
    u'value': 100
}

SDR_INT4 = {
    u'component_label': u'usage2',
    u'correlation_number': 4,
    u'customer': u'test_user',
    u'offering': {
        u'name': u'PayPerUse',
        u'organization': u'fdelavega',
        u'version': u'1.0'
    },
    u'record_type': u'event',
    u'time_stamp': datetime(2015, 9, 14, 10, 0, 3),
    u'unit': u'invocation',
    u'value': 100
}

SDR1 = deepcopy(SDR_INT1)
SDR1['time_stamp'] = unicode(SDR1['time_stamp'])

SDR2 = deepcopy(SDR_INT2)
SDR2['time_stamp'] = unicode(SDR2['time_stamp'])

SDR3 = deepcopy(SDR_INT3)
SDR3['time_stamp'] = unicode(SDR3['time_stamp'])

SDR4 = deepcopy(SDR_INT4)
SDR4['time_stamp'] = unicode(SDR4['time_stamp'])


class CDRRetrievingTestCase(TestCase):

    tags = ('sdrs')

    def setUp(self):
        # Create request
        self.factory = RequestFactory()

        # Create testing user
        self.user = User.objects.create_user(
            username='test_user',
            email='',
            password='passwd'
        )

        self.user.is_staff = True
        self.user.save()

        # Mock includes
        self._purchase_mock = MagicMock()
        self._purchase_mock.organization_owned = False
        self._purchase_mock.owner_organization = self.user.userprofile.current_organization

        views.Purchase = MagicMock()
        views.Purchase.objects.get.return_value = self._purchase_mock

    def tearDown(self):
        reload(views)

    def _add_pending(self):
        self._purchase_mock.contract.pending_sdrs = [deepcopy(SDR_INT1), deepcopy(SDR_INT2)]
        self._purchase_mock.contract.applied_sdrs = []

    def _add_applied(self):
        self._purchase_mock.contract.pending_sdrs = [deepcopy(SDR_INT3), deepcopy(SDR_INT4)]
        self._purchase_mock.contract.applied_sdrs = [deepcopy(SDR_INT1), deepcopy(SDR_INT2)]

    def _not_staff(self):
        self._add_pending()
        self.user.is_staff = False

    def _contract_error(self):
        self._purchase_mock.contract.side_effect = Exception('')

    def _contract_none(self):
        self._purchase_mock.contract = None

    def _forbidden(self):
        self.user.is_staff = False
        org = Organization.objects.create(name="Example")
        self.user.userprofile.current_organization = org
        self.user.userprofile.save()

    def _not_found(self):
        views.Purchase.objects.get.side_effect = Exception('')

    @parameterized.expand([
        ('basic', (200, [SDR1, SDR2]), _add_pending),
        ('applied_from_to', (200, [SDR2, SDR3]), _add_applied, "?from=2015-09-14 10:00:01.0&to=2015-09-14 10:00:02.0"),
        ('label', (200, [SDR4]), _add_applied, "?label=usage2"),
        ('not_staff', (200, [SDR1, SDR2]), _not_staff),
        ('contract_error', (200, []), _contract_error),
        ('contract_none', (200, []), _contract_none),
        ('forbidden', (403, {
            "result": "error",
            "message": "You are not authorized to read accounting info of the given purchase"
        }), _forbidden),
        ('not_found', (404, {
            "result": "error",
            "message": "There is not any purchase with reference aaaaa"
        }), _not_found),
        ('invalid_from', (400, {
            "result": "error",
            "message": 'Invalid "from" parameter, must be a datetime'
        }), None, "?from=2015:09:14 10:00:01.0"),
        ('invalid_to', (400, {
            "result": "error",
            "message": 'Invalid "to" parameter, must be a datetime'
        }), None, "?to=2015:09:14 10:00:01.0")
    ])
    def test_cdrs_retrieving(self, name, expected, side_effect=None, qstring=""):

        if side_effect is not None:
            side_effect(self)

        sdr_collection = views.ServiceRecordCollection(permitted_methods=("GET", "POST"))

        request = self.factory.get(
            '/api/contracting/aaaaa/accounting' + qstring,
            HTTP_ACCEPT='application/json; charset=utf-8'
        )
        request.user = self.user

        # Call the view
        response = sdr_collection.read(request, 'aaaaa')

        # Validate the response
        self.assertEqual(response.status_code, expected[0])
        body_response = json.loads(response.content)
        self.assertEquals(body_response, expected[1])

        # Validate calls
        views.Purchase.objects.get.assert_called_once_with(ref='aaaaa')
