from __future__ import absolute_import

import os
import json
import rdflib

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from charging_engine.charging_engine import ChargingEngine
from fiware_store.models import Purchase
from fiware_store.models import UserProfile
from fiware_store.models import Organization


class SinglePaymentChargingTestCase(TestCase):

    fixtures = ['single_payment.json']

    _to_delete = []

    def setUp(self):
        self._to_delete = []

    def tearDown(self):

        for f in self._to_delete:
            fil = os.path.join(settings.BASEDIR, f[1:])
            os.remove(fil)

        self._to_delete = []

    def test_basic_charging_single_payment(self):

        # Load model
        model = os.path.join(settings.BASEDIR, 'charging_engine')
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

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        charging_engine = ChargingEngine(purchase)

        charging_engine.resolve_charging(new_purchase=True)

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
        model = os.path.join(settings.BASEDIR, 'charging_engine')
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

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        charging_engine = ChargingEngine(purchase)

        charging_engine.resolve_charging(new_purchase=True)

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
