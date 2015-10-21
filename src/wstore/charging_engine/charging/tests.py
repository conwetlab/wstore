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

from nose_parameterized import parameterized

from django.test.utils import override_settings
from django.test import TestCase

from wstore.charging_engine.charging import cdr_manager
from wstore.models import Purchase, Organization


BASIC_EXP = [{
    'provider': 'test_organization',
    'service': 'test_offering 1.0',
    'defined_model': 'Single payment event',
    'correlation': '0',
    'purchase': '61004aba5e05acc115f022f0',
    'offering': 'test_offering 1.0',
    'product_class': 'test_organization/test_offering/1.0',
    'description': 'Single payment: 1 EUR',
    'cost_currency': 'EUR',
    'cost_value': '1',
    'tax_currency': 'EUR',
    'tax_value': '0.0',
    'country': '1',
    'customer': 'test_user',
    'event': 'use',
    'source': '1',
    'operator': '1',
    'time_stamp': u'2015-10-21 06:13:26.661650'
}]

INITIAL_EXP = [{
    'provider': 'test_organization',
    'service': 'test_offering 1.0',
    'defined_model': 'Single payment event',
    'correlation': '0',
    'purchase': '61004aba5e05acc115f022f0',
    'offering': 'test_offering 1.0',
    'product_class': 'test_organization/test_offering/1.0',
    'description': 'Single payment: 1 EUR',
    'cost_currency': 'EUR',
    'cost_value': '1',
    'tax_currency': 'EUR',
    'tax_value': '0.0',
    'country': '1',
    'customer': 'test_user',
    'event': 'use',
    'source': '1',
    'operator': '1',
    'time_stamp': u'2015-10-21 06:13:26.661650'
}, {
    'provider': 'test_organization',
    'service': 'test_offering 1.0',
    'defined_model': 'Subscription event',
    'correlation': '1',
    'purchase': '61004aba5e05acc115f022f0',
    'offering': 'test_offering 1.0',
    'product_class': 'test_organization/test_offering/1.0',
    'description': 'Subscription: 10 EUR per month',
    'cost_currency': 'EUR',
    'cost_value': '10',
    'tax_currency': 'EUR',
    'tax_value': '0.0',
    'country': '1',
    'customer': 'test_user',
    'event': 'use',
    'source': '1',
    'operator': '1',
    'time_stamp': u'2015-10-21 06:13:26.661650'
}]

USE_EXP = [{
    'provider': 'test_organization',
    'service': 'test_offering 1.0',
    'defined_model': 'Pay per use event',
    'correlation': '0',
    'purchase': '61004aba5e05acc115f022f0',
    'offering': 'test_offering 1.0',
    'product_class': 'test_organization/test_offering/1.0',
    'description': 'Fee per invocation, Consumption: 25',
    'cost_currency': 'EUR',
    'cost_value': '25.0',
    'tax_currency': 'EUR',
    'tax_value': '0.0',
    'country': '1',
    'customer': 'test_user',
    'event': 'use',
    'source': '1',
    'operator': '1',
    'time_stamp': u'2015-10-21 06:13:26.661650'
}]


class AdaptorWrapperThread:

    _context = None
    _url = None
    _cdr = None

    def __init__(self, context):
        self._context = context

    def __call__(self, url, cdr):
        self._url = url
        self._cdr = cdr
        return self

    def start(self):
        self._context._cdrs = self._cdr


@override_settings(STORE_NAME='wstore')
class CDRGenerationTestCase(TestCase):

    tags = ('cdr', )
    fixtures = ['cdr_generation.json']
    _cdrs = None

    @classmethod
    def setUpClass(cls):
        cdr_manager.RSSAdaptorThread = AdaptorWrapperThread(cls)
        super(CDRGenerationTestCase, cls).setUpClass()

    def setUp(self):
        cdr_manager.get_currency_code = lambda x: '1'

    def tearDown(self):
        self._cdrs = None
        self.maxDiff = None
        TestCase.tearDown(self)

    def _create_purchase(self):
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        org = Organization.objects.get(name="test_user")
        org.actor_id = "test_user"
        org.save()

        purchase.owner_organization = org
        purchase.save()

        return purchase

    @parameterized.expand([
        ('basic', {
            'single_payment': [{
               'title': 'example part',
               'unit': 'single_payment',
               'currency': 'EUR',
               'value': '1'
            }]
        }, BASIC_EXP),
        ('initial', {
            'single_payment': [{
               'title': 'example part',
               'unit': 'single_payment',
               'currency': 'EUR',
               'value': '1'
            }],
            'subscription': [{
                'title': 'example part2',
                'unit': 'per month',
                'currency': 'EUR',
                'value': '10'
            }]
        }, INITIAL_EXP),
        ('use', {
            'charges': [{
                'accounting': [{
                    'offering': {
                        'name': 'test_offering',
                        'organization': 'test_organization',
                        'version': '1.0'
                    },
                    'customer': 'test_user',
                    'value': '15',
                    'unit': 'invocation'
                }, {
                    'offering': {
                        'name': 'test_offering',
                        'organization': 'test_organization',
                        'version': '1.0'
                    },
                    'customer': 'test_user',
                    'value': '10',
                    'unit': 'invocation'
                }],
                'model': {
                    'title': 'example part',
                    'unit': 'invocation',
                    'currency': 'EUR',
                    'value': '1'
                },
                'price': 25.0
            }]
        }, USE_EXP)
    ])
    def test_cdr_generation(self, name, applied_parts, expected_result):
        purchase = self._create_purchase()

        manager = cdr_manager.CDRManager(purchase)
        manager.generate_cdr(applied_parts, u'2015-10-21 06:13:26.661650')

        self.assertEquals(self._cdrs, expected_result)
