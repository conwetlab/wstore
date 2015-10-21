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

from copy import deepcopy
from datetime import datetime
from nose_parameterized import parameterized

from django.test import TestCase
from django.core.exceptions import PermissionDenied

from wstore.models import Purchase, User, Organization
from wstore.charging_engine.accounting import sdr_manager


BASIC_SDR = {
    'offering': {
        'name': 'test_offering',
        'organization': 'test_organization',
        'version': '1.0'
    },
    'component_label': 'invocations',
    'customer': 'test_user',
    'correlation_number': '1',
    'time_stamp': '2015-10-20 17:31:57.838',
    'record_type': 'event',
    'value': '10',
    'unit': 'invocation'
}


class SDRManagerTestCase(TestCase):

    tags = ('sdr',)
    fixtures = ('payperuse.json', )

    def _side_create_applied(self):
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        sdr = deepcopy(BASIC_SDR)
        sdr['time_stamp'] = datetime.strptime(sdr['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')
        purchase.contract.applied_sdrs = [sdr]
        purchase.contract.save()

    def _side_create_pending(self):
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        sdr = deepcopy(BASIC_SDR)
        sdr['time_stamp'] = datetime.strptime(sdr['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')
        purchase.contract.pending_sdrs = [sdr]
        purchase.contract.save()

    def _side_purch_org(self):
        org = Organization.objects.get(name='test_organization1')
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        purchase.organization_owned = True
        purchase.owner_organization = org
        purchase.save()

    def _side_org_owned(self):
        user = User.objects.get(username='test_user2')
        org = Organization.objects.get(name='test_organization1')
        user.userprofile.current_organization = org
        user.userprofile.organizations = [{
            'organization': org.pk,
            'roles': ['customer', 'provider']
        }]
        user.userprofile.save()
        self._side_purch_org()

    def _modify_pricing(self, pricing):
        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        purchase.contract.pricing_model = pricing
        purchase.contract.save()

    def _side_inv_purchase(self):
        self._modify_pricing({
            'global_currency': 'EUR',
            'single_payment': [{
                'value': 10
            }]
        })

    def _side_inv_label(self):
        self._modify_pricing({
            'global_currency': 'EUR',
            'pay_per_use': [{
                'label': 'a label',
                'value': 10,
                'unit': 'call'
            }]
        })

    def _mod_inc_corr(self, sdr):
        sdr['correlation_number'] = 2
        sdr['time_stamp'] = '2015-10-20T17:31:57.838123'

    def _mod_set_org(self, sdr):
        sdr['customer'] = 'test_user2'

    def _mod_inv_time(self, sdr):
        self._mod_inc_corr(sdr)
        sdr['time_stamp'] = '1980-05-01 11:10:01.234'

    def _mod_inv_off(self, sdr):
        sdr['offering'] = {
            'name': 'test_offering2',
            'organization': 'test_organization',
            'version': '1.0'
        }

    @parameterized.expand([
        ('basic', ),
        ('applied',  0, 1, _mod_inc_corr, _side_create_applied),
        ('pending',  1, 2, _mod_inc_corr, _side_create_pending),
        ('org_owned', 0, 1, _mod_set_org, _side_org_owned),
        ('user_not_auth', 0, 1, _mod_set_org, None, PermissionDenied, 'The user has not acquired the offering'),
        ('user_org_not_auth', 0, 1, _mod_set_org, _side_purch_org, PermissionDenied, 'The user does not belong to the owner organization'),
        ('inv_corr', 0, 1, _mod_inc_corr, None, ValueError, 'Invalid correlation number, expected: 1'),
        ('inv_time', 0, 1, _mod_inv_time, _side_create_applied, ValueError, 'The provided timestamp specifies a lower timing than the last SDR received'),
        ('inv_offering', 0, 1, _mod_inv_off, None, PermissionDenied, 'The offering specified in the SDR is not the acquired offering'),
        ('inv_purch', 0, 1, None, _side_inv_purchase, ValueError, 'The pricing model of the offering does not define pay-per-use components'),
        ('inv_label', 0, 1, None, _side_inv_label, ValueError, 'The specified unit or component label is not included in the pricing model')
    ])
    def test_sdr_feeding(self, name, pos=0, pending=1, mod=None, side_effect=None, err_type=None, err_msg=None):

        sdr = deepcopy(BASIC_SDR)

        if mod is not None:
            mod(self, sdr)

        if side_effect is not None:
            side_effect(self)

        purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
        sdr_mng = sdr_manager.SDRManager(purchase)

        error = None
        try:
            sdr_mng.include_sdr(sdr)
        except Exception as e:
            error = e

        # Refresh the purchase
        if err_type is None:
            self.assertTrue(error is None)

            purchase = Purchase.objects.get(pk='61004aba5e05acc115f022f0')
            contract = purchase.contract

            self.assertEqual(len(contract.pending_sdrs), pending)

            loaded_sdr = contract.pending_sdrs[pos]

            self.assertEquals(loaded_sdr['offering']['organization'], sdr['offering']['organization'])
            self.assertEquals(loaded_sdr['component_label'], sdr['component_label'])
            self.assertEquals(loaded_sdr['customer'], sdr['customer'])
            self.assertEquals(loaded_sdr['correlation_number'], sdr['correlation_number'])
            self.assertEquals(loaded_sdr['time_stamp'], sdr['time_stamp'])
            self.assertEquals(loaded_sdr['record_type'], sdr['record_type'])
            self.assertEquals(loaded_sdr['value'], sdr['value'])
            self.assertEquals(loaded_sdr['unit'], sdr['unit'])
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)
