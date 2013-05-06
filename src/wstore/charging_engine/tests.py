from __future__ import absolute_import

import os
import json
import rdflib
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from wstore.charging_engine import charging_engine
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.models import Organization
#from wstore import charging_engine


def fake_renovation_date(unit):

    if unit == 'per month':
        return datetime(2013, 04, 01, 00, 00, 00)
    elif unit == 'per week':
        return datetime(2013, 03, 20, 00, 00, 00)


class FakePal():

    COUNTRY_CODES = (('SP', 'test country'),)

    def __init__(self):
        pass

    def ShortDate(self, year, month):
        return 0

    class PayPal():

        def __init__(self, usr, passwd, singn, url):
            pass

        def DoDirectPayment(self, **kwargs):
            pass

        def SetExpressCheckout(self, **kwargs):
            return {
                'TOKEN': ['11111111']
            }


class FakeThreading():

    class Timer():

        def __init__(self, time, handler):
            pass

        def start(self):
            pass


class SinglePaymentChargingTestCase(TestCase):

    fixtures = ['single_payment.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        charging_engine.paypal = FakePal()
        super(SinglePaymentChargingTestCase, cls).setUpClass()

    def setUp(self):
        self._to_delete = []

    def tearDown(self):

        for f in self._to_delete:
            fil = os.path.join(settings.BASEDIR, f[1:])
            os.remove(fil)

        self._to_delete = []

    def test_basic_charging_single_payment(self):

        # Load model
        model = os.path.join(settings.BASEDIR, 'wstore')
        model = os.path.join(model, 'charging_engine')
        model = os.path.join(model, 'test')
        model = os.path.join(model, 'basic_price.ttl')
        f = open(model, 'rb')
        graph = rdflib.Graph()
        graph.parse(data=f.read(), format='n3')
        f.close()

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

        offering = purchase.offering
        json_model = graph.serialize(format='json-ld')

        offering.offering_description = json.loads(json_model)
        offering.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)

        charging.resolve_charging(new_purchase=True)

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        bills = purchase.bill

        self.assertEqual(len(bills), 1)
        self._to_delete.append(bills[0])

        contract = purchase.contract
        charges = contract.charges

        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0]['cost'], 5)
        self.assertEqual(charges[0]['currency'], 'euros')
        self.assertEqual(charges[0]['concept'], 'initial charge')

        price_model = contract.pricing_model

        self.assertTrue('single_payment' in price_model)
        self.assertFalse('subscription' in price_model)
        self.assertFalse('pay_per_use' in price_model)

        self.assertEqual(len(price_model['single_payment']), 1)
        self.assertEqual(price_model['single_payment'][0]['title'], 'Price component 1')
        self.assertEqual(price_model['single_payment'][0]['value'], '5')

    def test_charging_single_payment_parts(self):

        # Load model
        model = os.path.join(settings.BASEDIR, 'wstore')
        model = os.path.join(model, 'charging_engine')
        model = os.path.join(model, 'test')
        model = os.path.join(model, 'complex_sin_price.ttl')
        f = open(model, 'rb')
        graph = rdflib.Graph()
        graph.parse(data=f.read(), format='n3')
        f.close()

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

        offering = purchase.offering
        json_model = graph.serialize(format='json-ld')

        offering.offering_description = json.loads(json_model)
        offering.save()

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)

        charging.resolve_charging(new_purchase=True)

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        bills = purchase.bill
        self.assertEqual(len(bills), 1)
        self._to_delete.append(bills[0])

        contract = purchase.contract
        charges = contract.charges

        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0]['cost'], 17)
        self.assertEqual(charges[0]['currency'], 'euros')
        self.assertEqual(charges[0]['concept'], 'initial charge')

        price_model = contract.pricing_model

        self.assertTrue('single_payment' in price_model)
        self.assertFalse('subscription' in price_model)
        self.assertFalse('pay_per_use' in price_model)

        self.assertEqual(len(price_model['single_payment']), 3)

        for pay in price_model['single_payment']:

            if pay['title'] == 'Price component 1':
                self.assertEqual(pay['title'], 'Price component 1')
                self.assertEqual(pay['value'], '5')

            elif pay['title'] == 'Price component 2':
                self.assertEqual(pay['title'], 'Price component 2')
                self.assertEqual(pay['value'], '5')

            elif pay['title'] == 'Price component 3':
                self.assertEqual(pay['title'], 'Price component 3')
                self.assertEqual(pay['value'], '7')


class SubscriptionChargingTestCase(TestCase):

    fixtures = ['subscription.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        charging_engine.paypal = FakePal()
        super(SubscriptionChargingTestCase, cls).setUpClass()

    def setUp(self):
        self._to_delete = []

    def tearDown(self):

        for f in self._to_delete:
            try:
                fil = os.path.join(settings.BASEDIR, f[1:])
                os.remove(fil)
            except:
                pass

        self._to_delete = []

    def test_basic_subscription_charging(self):

        # Load model
        model = os.path.join(settings.BASEDIR, 'wstore')
        model = os.path.join(model, 'charging_engine')
        model = os.path.join(model, 'test')
        model = os.path.join(model, 'basic_subs.ttl')
        f = open(model, 'rb')
        graph = rdflib.Graph()
        graph.parse(data=f.read(), format='n3')
        f.close()

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

        offering = purchase.offering
        json_model = graph.serialize(format='json-ld')

        offering.offering_description = json.loads(json_model)
        offering.save()
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')

        credit_card = {
            'type': 'Visa',
            'number': '1234123412341234',
            'expire_year': '2018',
            'expire_month': '2',
            'cvv2': '111',
        }

        charging = charging_engine.ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)
        charging._calculate_renovation_date = fake_renovation_date

        charging.resolve_charging(new_purchase=True)
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        self._to_delete.extend(purchase.bill)
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['cost'], 10)
        self.assertEqual(contract.charges[0]['currency'], 'euros')
        self.assertEqual(contract.charges[0]['concept'], 'initial charge')

        pricing_model = contract.pricing_model

        self.assertTrue('subscription' in pricing_model)
        self.assertFalse('single_payment' in pricing_model)
        self.assertFalse('pay_per_use' in pricing_model)

        for sub in pricing_model['subscription']:
            if sub['title'] == 'Price component 1':
                self.assertEqual(sub['value'], '5')
                self.assertEqual(sub['unit'], 'per month')
                self.assertEqual(str(sub['renovation_date']), '2013-04-01 00:00:00')
            else:
                self.assertEqual(sub['title'], 'Price component 2')
                self.assertEqual(sub['value'], '5')
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

        charging.resolve_charging()
        purchase = Purchase.objects.get(pk="61005a1a8205ac3115111111")
        self._to_delete.extend(purchase.bill)
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 2)
        self.assertEqual(contract.charges[0]['cost'], 10)
        self.assertEqual(contract.charges[0]['currency'], 'euros')
        self.assertEqual(contract.charges[0]['concept'], 'initial')
        self.assertEqual(contract.charges[1]['cost'], 10)
        self.assertEqual(contract.charges[1]['currency'], 'euros')
        self.assertEqual(contract.charges[1]['concept'], 'Renovation')

        pricing_model = contract.pricing_model

        self.assertTrue('subscription' in pricing_model)
        self.assertFalse('single_payment' in pricing_model)
        self.assertFalse('pay_per_use' in pricing_model)

        for sub in pricing_model['subscription']:
            if sub['title'] == 'price component 1':
                self.assertEqual(sub['value'], '5')
                self.assertEqual(sub['unit'], 'per month')
                self.assertEqual(str(sub['renovation_date']), '2013-04-01 00:00:00')
            else:
                self.assertEqual(sub['title'], 'price component 2')
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

        charging.resolve_charging()
        purchase = Purchase.objects.get(pk='61005aba8e06ac2015f022f0')
        self._to_delete.extend(purchase.bill)
        contract = purchase.contract

        self.assertEqual(len(contract.charges), 2)
        self.assertEqual(contract.charges[0]['cost'], 10)
        self.assertEqual(contract.charges[0]['currency'], 'euros')
        self.assertEqual(contract.charges[0]['concept'], 'initial')
        self.assertEqual(contract.charges[1]['cost'], 5)
        self.assertEqual(contract.charges[1]['currency'], 'euros')
        self.assertEqual(contract.charges[1]['concept'], 'Renovation')

        pricing_model = contract.pricing_model

        self.assertTrue('subscription' in pricing_model)
        self.assertFalse('single_payment' in pricing_model)
        self.assertFalse('pay_per_use' in pricing_model)

        for s in pricing_model['subscription']:
            if s['title'] == 'price component 1':
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


class AsynchronousPaymentTestCase(TestCase):

    fixtures = ['async.json']

    _to_delete = []

    @classmethod
    def setUpClass(cls):
        charging_engine.paypal = FakePal()
        charging_engine.threading = FakeThreading()
        super(AsynchronousPaymentTestCase, cls).setUpClass()

    def setUp(self):
        self._to_delete = []

    def tearDown(self):

        for f in self._to_delete:
            fil = os.path.join(settings.BASEDIR, f[1:])
            os.remove(fil)

        self._to_delete = []

    def test_basic_asynchronous_payment(self):

        # Load model
        model = os.path.join(settings.BASEDIR, 'wstore')
        model = os.path.join(model, 'charging_engine')
        model = os.path.join(model, 'test')
        model = os.path.join(model, 'basic_price.ttl')
        f = open(model, 'rb')
        graph = rdflib.Graph()
        graph.parse(data=f.read(), format='n3')
        f.close()

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

        offering = purchase.offering
        json_model = graph.serialize(format='json-ld')

        offering.offering_description = json.loads(json_model)
        offering.save()

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
        self.assertEqual(model['single_payment'][0]['title'], 'Price component 1')
        self.assertEqual(model['single_payment'][0]['value'], '5')

        # Second step
        charging = charging_engine.ChargingEngine(purchase)
        charging.end_charging(contract.pending_payment['price'], contract.pending_payment['concept'], contract.pending_payment['related_model'])

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        self.assertEqual(purchase.state, 'paid')
        bills = purchase.bill

        self.assertEqual(len(bills), 1)
        self._to_delete.append(bills[0])

        contract = purchase.contract
        self.assertEqual(len(contract.charges), 1)

        self.assertEqual(contract.charges[0]['cost'], '5.00')
        self.assertEqual(contract.charges[0]['currency'], 'euros')
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

        connection = MongoClient()
        db = connection[settings.DATABASES['default']['NAME']]

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

        connection = MongoClient()
        db = connection[settings.DATABASES['default']['NAME']]

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
