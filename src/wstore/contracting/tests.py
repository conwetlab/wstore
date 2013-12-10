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

import json
from mock import MagicMock
from urllib2 import HTTPError

from django.test import TestCase
from django.contrib.auth.models import User

from wstore.contracting import purchases_management
from wstore.contracting.purchase_rollback import rollback
from wstore.contracting import notify_provider
from wstore.models import Offering
from wstore.models import Organization
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.charging_engine.models import Contract
from social_auth.db.django_models import UserSocialAuth


__test__ = False


class FakeChargingEngine:
    def __init__(self, purchase, payment_method=None, credit_card=None):
        pass

    def resolve_charging(self, new_purchase):
        pass


def fake_generate_bill():
    pass


class PurchasesCreationTestCase(TestCase):

    tags = ('fiware-ut-16',)
    fixtures = ['purch_creat.json']

    @classmethod
    def setUpClass(cls):
        purchases_management.generate_bill = fake_generate_bill
        purchases_management.ChargingEngine = FakeChargingEngine
        purchases_management.ChargingEngine.resolve_charging = MagicMock(name='resolve_charging')
        super(PurchasesCreationTestCase, cls).setUpClass()

    def setUp(self):
        purchases_management.ChargingEngine.resolve_charging.reset_mock()
        purchases_management.ChargingEngine.resolve_charging.return_value = None

    def test_basic_purchase_creation(self):

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')

        tax_address = {
            'street': 'test street',
            'postal': '28000',
            'city': 'test city',
            'country': 'test country'
        }

        user_profile = UserProfile.objects.get(user=user)
        user_profile.tax_address = tax_address
        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        payment_info = {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            }
        }

        purchase = purchases_management.create_purchase(user, offering, payment_info=payment_info)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, False)
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        purchase = Purchase.objects.get(customer=user, offering=offering)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, False)
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        user_profile = UserProfile.objects.get(user=user)
        self.assertEqual(len(user_profile.offerings_purchased), 1)
        self.assertEqual(user_profile.offerings_purchased[0], offering.pk)

    def test_purchase_creation_org_owned(self):

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')

        tax_address = {
            'street': 'test street',
            'postal': '28000',
            'city': 'test city',
            'country': 'test country'
        }

        user_profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        org.tax_address = tax_address
        org.save()
        user_profile.current_organization = org
        user_profile.organizations = [{
            'organization': org.pk,
            'roles': ['customer']
        }]
        user_profile.save()

        payment_info = {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            }
        }

        purchase = purchases_management.create_purchase(user, offering, True, payment_info=payment_info)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, True)
        self.assertEqual(purchase.owner_organization.name, 'test_organization')
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        organization = Organization.objects.get(name='test_organization')
        self.assertEqual(len(organization.offerings_purchased), 1)
        self.assertEqual(organization.offerings_purchased[0], offering.pk)

    def test_purchase_creation_tax_address(self):

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')

        payment_info = {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }

        user_profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        purchase = purchases_management.create_purchase(user, offering, payment_info=payment_info)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, False)
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        purchase = Purchase.objects.get(customer=user, offering=offering)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, False)
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        user_profile = UserProfile.objects.get(user=user)
        self.assertEqual(len(user_profile.offerings_purchased), 1)
        self.assertEqual(user_profile.offerings_purchased[0], offering.pk)

    def test_purchase_non_published_off(self):

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering2')

        payment_info = {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }

        error = False
        msg = None

        try:
            purchases_management.create_purchase(user, offering, payment_info=payment_info)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, "This offering can't be purchased")

    def test_purchase_already_purchased(self):

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering3')
        user_profile = UserProfile.objects.get(user=user)
        user_profile.offerings_purchased = ['81000aba8e05ac2115f022f0']
        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        payment_info = {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }

        error = False
        msg = None

        try:
            purchases_management.create_purchase(user, offering, payment_info=payment_info)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, "The offering has been already purchased")

    def test_purchase_exeptions(self):

        # Load test info
        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')

        error_messages = [
            'The customer does not have a tax address',
            'The tax address is not valid',
            'Invalid credit card info',
            'Invalid payment method',
            'The customer does not have payment info'
        ]
        payment_info = [{
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            }
        }, {
           'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }, {
            'payment_method': 'credit_card',
            'credit_card': {
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }, {
            'payment_method': 'credit',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }, {
            'payment_method': 'credit_card',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }
        ]
        # Test exceptions
        for i in range(0, 3):
            error = False
            msg = None

            try:
                purchases_management.create_purchase(user, offering, payment_info=payment_info[i])
            except Exception, e:
                error = True
                msg = e.message

            self.assertTrue(error)
            self.assertEqual(msg, error_messages[i])

    def test_purchase_creation_paypal(self):
        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')
        payment_info = {
            'payment_method': 'paypal',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }
        purchase = purchases_management.create_purchase(user, offering, payment_info=payment_info)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, False)
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        purchase = Purchase.objects.get(customer=user, offering=offering)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, False)
        self.assertEqual(purchase.offering_id, offering.pk)
        self.assertEqual(purchase.tax_address['street'], 'test street')
        self.assertEqual(purchase.tax_address['postal'], '28000')
        self.assertEqual(purchase.tax_address['city'], 'test city')
        self.assertEqual(purchase.tax_address['country'], 'test country')

        user_profile = UserProfile.objects.get(user=user)
        self.assertEqual(len(user_profile.offerings_purchased), 1)
        self.assertEqual(user_profile.offerings_purchased[0], offering.pk)

    def test_purchase_creation_organization_payment(self):
        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')

        user_profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        org.payment_info = {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
        }
        org.save()
        user_profile.current_organization = org
        user_profile.organizations = [{
            'organization': org.pk,
            'roles': ['customer']
        }]
        user_profile.save()
        payment_info = {
            'payment_method': 'credit_card',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            }
        }

        purchases_management.ChargingEngine.resolve_charging.return_value = 'http://paypal.com/redirect'
        redirect_url = purchases_management.create_purchase(user, offering, True, payment_info=payment_info)
        purchases_management.ChargingEngine.resolve_charging.assert_called_once_with(new_purchase=True)

        self.assertEquals(redirect_url, 'http://paypal.com/redirect')


class PurchaseRollbackTestCase(TestCase):

    fixtures = ['purch_rollback.json']

    def test_rollback_not_paid_exeption(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        rollback(purchase)

        # Check the final state of the database
        error = False
        msg = None
        try:
            Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Purchase matching query does not exist.')

    def test_rollback_not_paid_contract(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f02111')
        rollback(purchase)

        # Check the final state of the database
        error_purch = False
        error_cont = False
        msg_purch = None
        msg_cont = None
        try:
            Purchase.objects.get(pk='61005aba8e05ac2115f02111')
        except Exception, e:
            error_purch = True
            msg_purch = e.message

        try:
            Contract.objects.get(pk='6100023a7825a622562020f9')
        except Exception, e:
            error_cont = True
            msg_cont = e.message

        self.assertTrue(error_purch)
        self.assertEqual(msg_purch, 'Purchase matching query does not exist.')
        self.assertTrue(error_cont)
        self.assertEqual(msg_cont, 'Contract matching query does not exist.')

    def test_rollback_not_paid_renovation(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f02222')
        rollback(purchase)

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f02222')

        self.assertEqual(purchase.state, 'paid')

        contract = purchase.contract
        self.assertEqual(len(contract.charges), 1)
        self.assertEqual(contract.charges[0]['concept'], 'initial')

    def test_rollback_paid_exeption(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f02333')
        rollback(purchase)

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f02333')

        self.assertEqual(purchase.state, 'paid')

        contract = purchase.contract
        self.assertEqual(len(contract.charges), 2)
        self.assertEqual(contract.charges[0]['concept'], 'initial')
        self.assertEqual(contract.charges[1]['concept'], 'renovation')


class FakeUrlib2Notify():

    _opener = None

    def __init__(self):
        self._opener = self.Opener(self.Response())

    def build_opener(self):
        return self._opener

    class Opener():

        _response = None
        _method = None
        _header = None
        _body = None
        _url = None

        def __init__(self, response):
            self._response = response

        def open(self, request):
            if  request.get_header('Authorization') == 'Bearer bca':
                raise HTTPError('', 401, '', None, None)

            self._method = request.get_method()
            self._header = request.get_header('Content-type')
            self._body = request.data
            self._url = request.get_full_url()

            return self._response

    class Response():
        url = 'http://response.com/'
        code = 201


class ProviderNotificationTestCase(TestCase):

    fixtures = ['notify.json']

    _urllib = None

    @classmethod
    def setUpClass(cls):
        cls._urllib = FakeUrlib2Notify()
        notify_provider.urllib2 = cls._urllib
        super(ProviderNotificationTestCase, cls).setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')

    def test_provider_notification(self):

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        notify_provider.notify_provider(purchase)

        opener = self._urllib._opener

        content = json.loads(opener._body)

        self.assertEqual(content['offering']['name'], 'test_offering')
        self.assertEqual(content['offering']['organization'], 'test_organization')
        self.assertEqual(content['offering']['version'], '1.0')

        self.assertEqual(content['customer'], 'test_organization1')
        self.assertEqual(content['reference'], '61005aba8e05ac2115f022f0')

    def test_identity_manager_notification(self):

        from django.conf import settings
        settings.OILAUTH = True
        
        # Mock purchase info
        purchase = MagicMock()
        purchase.offering.notification_url = ''
        purchase.offering.applications = [{
            'id': 1,
            'name': 'test_app1'
        }]
        purchase.organization_owned = False
        purchase.offering.owner_organization.name = 'test_user'
        purchase.offering.version = '1.0'
        purchase.offering.name = 'test_offering'
        purchase.ref = '11111'

        self.user.userprofile.actor_id = 1
        self.user.userprofile.access_token = 'aaa'
        self.user.userprofile.save()
        purchase.customer = self.user

        notify_provider.notify_provider(purchase)
        opener = self._urllib._opener

        content = json.loads(opener._body)

        self.assertEquals(len(content['applications']), 1)
        self.assertEquals(content['applications'][0]['id'], 1)
        self.assertEquals(content['applications'][0]['name'], 'test_app1')
        self.assertEquals(content['customer'], 1)
        

    test_identity_manager_notification.tags = ('fiware-ut-23',)

    def test_identity_manager_notification_org(self):

        from django.conf import settings
        settings.OILAUTH = True
        
        # Mock purchase info
        purchase = MagicMock()
        purchase.offering.notification_url = ''
        purchase.offering.applications = [{
            'id': 1,
            'name': 'test_app1'
        }]
        purchase.organization_owned = True
        purchase.offering.owner_organization.name = 'test_user'
        purchase.owner_organization.actor_id = 2
        purchase.offering.version = '1.0'
        purchase.offering.name = 'test_offering'
        purchase.ref = '11111'

        self.user.userprofile.access_token = 'aaa'
        self.user.userprofile.save()
        purchase.customer = self.user

        notify_provider.notify_provider(purchase)
        opener = self._urllib._opener

        content = json.loads(opener._body)

        self.assertEquals(len(content['applications']), 1)
        self.assertEquals(content['applications'][0]['id'], 1)
        self.assertEquals(content['applications'][0]['name'], 'test_app1')
        self.assertEquals(content['customer'], 2)

    test_identity_manager_notification_org.tags = ('fiware-ut-23',)

    def test_identity_manager_notification_token_refresh(self):

        from django.conf import settings
        settings.OILAUTH = True
        
        # Mock purchase info
        purchase = MagicMock()
        purchase.offering.notification_url = ''
        purchase.offering.applications = [{
            'id': 1,
            'name': 'test_app1'
        }]
        purchase.organization_owned = True
        purchase.offering.owner_organization.name = 'test_user'
        purchase.owner_organization.actor_id = 2
        purchase.offering.version = '1.0'
        purchase.offering.name = 'test_offering'
        purchase.ref = '11111'

        self.user.userprofile.access_token = 'bca'
        self.user.userprofile.save()

        # Mock social auth methods
        UserSocialAuth.refresh_token = MagicMock()
        user_social_auth = UserSocialAuth.objects.create(user=self.user, provider='fiware')

        user_social_auth.extra_data = {
            'access_token': 'bbb',
            'refresh_token': 'ccc'
        }

        user_social_auth.save()
        self.user.social_auth = [user_social_auth]

        purchase.customer = self.user

        # Call the tested method
        notify_provider.notify_provider(purchase)
        opener = self._urllib._opener

        content = json.loads(opener._body)

        UserSocialAuth.refresh_token.assert_any_call()
        self.assertEquals(len(content['applications']), 1)
        self.assertEquals(content['applications'][0]['id'], 1)
        self.assertEquals(content['applications'][0]['name'], 'test_app1')
        self.assertEquals(content['customer'], 2)

    test_identity_manager_notification_org.tags = ('fiware-ut-23',)

    test_identity_manager_notification_token_refresh.tags = ('fiware-ut-23',)