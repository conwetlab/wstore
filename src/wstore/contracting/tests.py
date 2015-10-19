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

from __future__ import unicode_literals

import json
import types
from mock import MagicMock
from urllib2 import HTTPError
from nose_parameterized import parameterized

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.exceptions import PermissionDenied
from social_auth.db.django_models import UserSocialAuth

import wstore.contracting.purchase_rollback
from wstore.contracting import purchases_management
from wstore.contracting import purchase_rollback

from wstore.contracting import notify_provider
from wstore.models import Offering, Context
from wstore.models import Organization
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.charging_engine.models import Contract
from wstore.contracting import views
from wstore.keyrock_backends import keyrock_backend_v1


__test__ = False


class FakeChargingEngine:
    def __init__(self, purchase, payment_method=None, credit_card=None, plan=None):
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

        # Save the reference of the decorators
        cls._old_roll = types.FunctionType(
            purchase_rollback.rollback.func_code,
            purchase_rollback.rollback.func_globals,
            name=purchase_rollback.rollback.func_name,
            argdefs=purchase_rollback.rollback.func_defaults,
            closure=purchase_rollback.rollback.func_closure
        )

        # Mock class decorators
        wstore.contracting.purchase_rollback.rollback = MagicMock()

        reload(purchases_management)
        # Mock purchases rollback
        super(PurchasesCreationTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        wstore.contracting.purchase_rollback.rollback = cls._old_roll
        super(PurchasesCreationTestCase, cls).tearDownClass()

    def setUp(self):
        purchases_management.ChargingEngine.resolve_charging = MagicMock()
        purchases_management.ChargingEngine.resolve_charging.return_value = None
        purchases_management.SearchEngine = MagicMock()
        se_obj = MagicMock()
        purchases_management.SearchEngine.return_value = se_obj
        usdl_info = {
            'name': 'test_offering',
            'base_id': 'pk',
            'image_url': '/media/test_image.png',
            'pricing': {
                'price_plans': []
            },
            'description': 'test offering',
            'abstract': 'test offering'
        }
        self._load_usdl(usdl_info)

    def _open_offering(self):
        offering = Offering.objects.get(name='test_offering')
        offering.open = True
        offering.save()

    def _fill_user_payment(self):
        user = User.objects.get(username='test_user')
        user.userprofile.payment_info = {
            'number': '1234123412341234',
            'type': 'Visa',
            'expire_year': '2018',
            'expire_month': '3',
            'cvv2': '111'
        }
        user.userprofile.save()

    def _load_usdl(self, usdl_info):
        # Load offering description to test offering
        offering = Offering.objects.get(name='test_offering')
        offering.offering_description = usdl_info
        offering.save()

    def _set_legal(self):
        usdl_info = {
            'name': 'test_offering',
            'base_id': 'pk',
            'image_url': '/media/test_image.png',
            'pricing': {
                'price_plans': []
            },
            'description': 'test offering',
            'abstract': 'test offering',
            'legal': {
                'title': 'terms and conditions',
                'text': 'this are the applied terms and conditions'
            }
        }
        self._load_usdl(usdl_info)

    def _non_published(self):
        offering = Offering.objects.get(name='test_offering')
        offering.state = 'uploaded'
        offering.save()

    def _already_purchased(self):
        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')
        user.userprofile.offerings_purchased = [offering.pk]
        user.userprofile.save()

    @parameterized.expand([
        ('invalid_payment', None, False, {
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'province': 'test_province',
                'country': 'test country'
            },
            'payment_method': 'incorrect'
        }, ValueError, 'Invalid payment method'),
        ('user_payment', _fill_user_payment, False, {
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'province': 'test_province',
                'country': 'test country'
            },
            'payment_method': 'credit_card',
            'plan': 'update'
        }),
        ('user_payment_no_info', None, False, {
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'province': 'test_province',
                'country': 'test country'
            },
            'payment_method': 'credit_card',
            'plan': 'update'
        }, Exception, 'The customer does not have payment info'),
        ('open_offering', _open_offering, False, None, PermissionDenied, 'Open offerings cannot be purchased'),
        ('no_tax_address', None, False, {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            }
        }, ValueError, 'The customer does not have a tax address'),
        ('invalid_tax_address', None, False, {
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
        }, ValueError, 'Missing a required field in the tax address. It must contain street, postal, city, province and country'),
        ('invalid_tax_address_2', None, False, {
            'payment_method': 'credit_card',
            'credit_card': {
                'number': '1234123412341234',
                'type': 'Visa',
                'expire_year': '2018',
                'expire_month': '3',
                'cvv2': '111'
            },
            'tax_address': {
                'street': '',
                'postal': '28000',
                'city': 'test city',
                'province': 'test_province',
                'country': 'test country'
            }
        }, ValueError, 'Missing a required field in the tax address. It must contain street, postal, city, province and country'),
        ('invalid_card_info', None, False, {
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
                'province': 'test_province',
                'country': 'test country'
            }
        }, ValueError, 'Invalid credit card info'),
        ('conditions', _set_legal, False, {
            'payment_method': 'paypal',
            'accepted': False
        }, PermissionDenied, 'You must accept the terms and conditions of the offering to acquire it'),
        ('non_published', _non_published, False, {
            'payment_method': 'paypal',
            'accepted': False
        }, PermissionDenied, "This offering can't be purchased"),
        ('already_purchased', _already_purchased, False, {
            'payment_method': 'paypal',
            'accepted': False
        }, PermissionDenied, 'The offering has been already purchased')
    ])
    def test_purchase_creation(self, name, side_effect, org_owned=False, payment_info=None, err_type=None, err_msg=None):

        if side_effect:
            side_effect(self)

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering')

        error = None
        try:
            purchase = purchases_management.create_purchase(user, offering, org_owned, payment_info)
        except Exception as e:
            error = e

        if not err_type:
            # Check that no error occurs
            self.assertEquals(error, None)

            # Check purchase information
            self.assertEqual(purchase.customer.username, 'test_user')
            self.assertEqual(purchase.owner_organization.name, 'test_user')
            self.assertEqual(purchase.organization_owned, False)
            self.assertEqual(purchase.offering_id, offering.pk)
            self.assertEqual(purchase.tax_address['street'], 'test street')
            self.assertEqual(purchase.tax_address['postal'], '28000')
            self.assertEqual(purchase.tax_address['city'], 'test city')
            self.assertEqual(purchase.tax_address['country'], 'test country')

            user_profile = UserProfile.objects.get(user=user)
            self.assertEqual(len(user_profile.offerings_purchased), 1)
            self.assertEqual(user_profile.offerings_purchased[0], offering.pk)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


class PurchaseRollbackTestCase(TestCase):

    fixtures = ['purch_rollback.json']

    def setUp(self):
        se_object = MagicMock()
        purchase_rollback.SearchEngine = MagicMock()
        purchase_rollback.SearchEngine.return_value = se_object

    def test_rollback_not_paid_exeption(self):

        user = User.objects.get(pk='51070aba8e05cc2115f022f9')
        profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(pk='91000aba8e06ac2115f022f0')
        profile.organization = org
        profile.save()

        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')
        purchase_rollback.rollback(purchase)

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
        purchase_rollback.rollback(purchase)

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
        purchase_rollback.rollback(purchase)

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
        purchase_rollback.rollback(purchase)

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
            if request.get_header('Authorization') == 'Bearer bca':
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
    tags = ('prov-not',)

    _urllib = None

    @classmethod
    def setUpClass(cls):
        cls._urllib = FakeUrlib2Notify()
        notify_provider.urllib2 = cls._urllib
        cls.prev_value = settings.OILAUTH
        super(ProviderNotificationTestCase, cls).setUpClass()

    def setUp(self):
        notify_provider.notify_acquisition = MagicMock(name="notify_acquisition")
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        self.user.userprofile.user = self.user
        self.user.userprofile.save()
        settings.OILAUTH = self.prev_value

    @classmethod
    def tearDownClass(cls):
        reload(keyrock_backend_v1)
        settings.OILAUTH = cls.prev_value
        super(ProviderNotificationTestCase, cls).tearDownClass()

    def test_provider_notification(self):

        settings.OILAUTH = False
        notify_provider.requests = MagicMock(name="requests")
        purchase = Purchase.objects.get(pk='61005aba8e05ac2115f022f0')

        expected_data = {
            'offering':  {
                'name': 'test_offering',
                'organization': 'test_organization',
                'version': '1.0'
            },
            'customer': 'test_organization1',
            'reference': '61005aba8e05ac2115f022f0',
            'resources': [{
                "url": "http://antares.ls.fi.upm.es:8000/media/resources/test_user__test_resource__1.0",
                "version": "1.0",
                "name": "test_resource",
                "content_type": ""
            }]
        }

        headers = {
            'Content-type': 'application/json'
        }
        notify_provider.notify_provider(purchase)
        notify_provider.requests.post.assert_called_with(
            purchase.offering.notification_url,
            data=json.dumps(expected_data),
            headers=headers,
            cert=(settings.NOTIF_CERT_FILE, settings.NOTIF_CERT_KEY_FILE)
        )

    def _build_mock_purchase(self, org_data):
        # Mock purchase info
        purchase = MagicMock()
        purchase.offering.notification_url = ''
        purchase.offering.applications = [{
            'id': 1,
            'name': 'test_app1'
        }]

        purchase.organization_owned = org_data['owned']
        purchase.owner_organization.actor_id = org_data['actor_id']

        purchase.owner_organization.name = 'test_user'
        purchase.offering.owner_organization.name = 'test_user'
        purchase.offering.version = '1.0'
        purchase.offering.name = 'test_offering'
        purchase.ref = '11111'

        self.user.userprofile.actor_id = 1
        self.user.userprofile.access_token = 'aaa'
        self.user.userprofile.save()
        purchase.customer = self.user

        return purchase

    def _set_expired_token(self):
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

    @parameterized.expand([
        ('basic', {
            'owned': False,
            'actor_id': 1
        }),
        ('org', {
            'owned': False,
            'actor_id': 1
        }),
        ('refresh', {
            'owned': False,
            'actor_id': 1
        }, True)
    ])
    def test_identity_manager_notification_v1(self, name, org_data, refresh=False):

        keyrock_backend_v1.urllib2 = FakeUrlib2Notify()

        settings.OILAUTH = True

        purchase = self._build_mock_purchase(org_data)

        if refresh:
            self._set_expired_token()

        keyrock_backend_v1.notify_acquisition(purchase)
        opener = keyrock_backend_v1.urllib2._opener

        content = json.loads(opener._body)

        if refresh:
            UserSocialAuth.refresh_token.assert_any_call()

        self.assertEquals(len(content['applications']), 1)
        self.assertEquals(content['applications'][0]['id'], 1)
        self.assertEquals(content['applications'][0]['name'], 'test_app1')
        self.assertEquals(content['customer'], org_data['actor_id'])


class UpdatingPurchasesTestCase(TestCase):

    tags = ('fiware-ut-28',)
    fixtures = ('multiple_plan.json',)

    @classmethod
    def setUpClass(cls):
        cls._old_context = Context
        super(UpdatingPurchasesTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        Context = cls._old_context
        super(UpdatingPurchasesTestCase, cls).tearDownClass()

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        self._user = User.objects.get(username='test_user')

    def test_basic_purchase_offering_update(self):
        # Get context
        cnt = Context.objects.all()[0]
        cnt.allowed_currencies = {
            "default": "EUR",
            "allowed": [{
                "currency": "EUR",
                "in_use": True
            }]
        }
        cnt.save()
        self._user.userprofile.offerings_purchased.append('61000aba8e05ac2115f022f9')
        # Create the request
        data = {
            'offering': {
                'organization': 'test_organization',
                'name': 'test_offering',
                'version': '1.1'
            },
            'plan_label': 'update',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment': {
                'method': 'paypal'
            }
        }
        request = self.factory.post(
            '/api/contracting/',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        request.user = self._user

        # Test purchase view
        views.create_purchase = MagicMock(name='create_purchase')
        offering = Offering.objects.get(pk="71000aba8e05ac2115f022ff")

        from datetime import datetime
        purchase = Purchase.objects.create(
            customer=self._user,
            date=datetime.now(),
            offering=offering,
            organization_owned=False,
            state='paid',
            tax_address={
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            bill=['/media/bills/11111111111.pdf']
        )
        views.create_purchase.return_value = purchase

        views.get_current_site = MagicMock(name='get_current_site')
        views.get_current_site.return_value = Site.objects.get(name='antares')
        views.Context.objects.get = MagicMock(name='get')
        context = MagicMock()
        context.user_refs = []
        views.Context.objects.get.return_value = context

        purchase_collection = views.PurchaseCollection(permitted_methods=('POST',))

        response = purchase_collection.create(request)

        # Check response
        body_response = json.loads(response.content)
        self.assertEquals(len(body_response['bill']), 1)
        self.assertEquals(body_response['bill'][0], '/media/bills/11111111111.pdf')
        payment_info = {
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment_method': 'paypal',
            'plan': 'update',
            'accepted': False
        }
        views.create_purchase.assert_called_once_with(self._user, offering, org_owned=False, payment_info=payment_info)

        offering.offering_description = {
            'pricing': {
                'price_plans': []
            }
        }

        offering.save()

        from wstore.charging_engine.charging_engine import ChargingEngine
        charging = ChargingEngine(purchase, payment_method='paypal', plan='update')
        charging._create_purchase_contract()

        # Refresh purchase
        purchase = Purchase.objects.get(pk=purchase.pk)
        contract = purchase.contract

        self.assertFalse('single_payment' in contract.pricing_model)
        self.assertFalse('subscription' in contract.pricing_model)
        self.assertFalse('pay_per_use' in contract.pricing_model)

    def test_purchase_offering_update_payment(self):

        current_org = Organization.objects.get(pk="91000aba8e06ac2199999999")
        current_org.offerings_purchased.append('61000aba8e05ac2115f022f9')
        self._user.userprofile.current_organization = current_org

        self._user.userprofile.get_current_roles = MagicMock()
        self._user.userprofile.get_current_roles.return_value = ['customer']
        self._user.userprofile.save()

        # Create the request
        data = {
            'offering': {
                'organization': 'test_organization',
                'name': 'test_offering',
                'version': '1.1'
            },
            'plan_label': 'update',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment': {
                'method': 'paypal'
            }
        }
        request = self.factory.post(
            '/api/contracting/',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        request.user = self._user

        # Test purchase view
        views.create_purchase = MagicMock(name='create_purchase')
        offering = Offering.objects.get(pk="71000aba8e05ac2115f022ff")

        from datetime import datetime
        purchase = Purchase.objects.create(
            customer=self._user,
            date=datetime.now(),
            offering=offering,
            organization_owned=True,
            state='paid',
            tax_address={
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            bill=['/media/bills/11111111111.pdf']
        )
        views.create_purchase.return_value = purchase

        views.get_current_site = MagicMock(name='get_current_site')
        views.get_current_site.return_value = Site.objects.get(name='antares')
        views.Context.objects.get = MagicMock(name='get')
        context = MagicMock()
        context.user_refs = []
        views.Context.objects.get.return_value = context

        purchase_collection = views.PurchaseCollection(permitted_methods=('POST',))

        response = purchase_collection.create(request)

        # Check response
        body_response = json.loads(response.content)
        self.assertEquals(len(body_response['bill']), 1)
        self.assertEquals(body_response['bill'][0], '/media/bills/11111111111.pdf')
        payment_info = {
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment_method': 'paypal',
            'plan': 'update',
            'accepted': False
        }
        views.create_purchase.assert_called_once_with(self._user, offering, org_owned=True, payment_info=payment_info)

        # Test Contract creation
        offering.offering_description = {
            'pricing': {
                'price_plans': [{
                    'title': 'Price plan',
                    'currency': 'EUR',
                    'price_components': [{
                        'label': 'Price component update',
                        'unit': 'single payment',
                        'value': '1.0'
                    }]
                }]
            }
        }
        offering.save()

        from wstore.charging_engine.charging_engine import ChargingEngine
        charging = ChargingEngine(purchase, payment_method='paypal', plan='update')
        charging._create_purchase_contract()

        # Refresh purchase
        purchase = Purchase.objects.get(pk=purchase.pk)
        contract = purchase.contract

        # Check contract pricing model
        self.assertTrue('single_payment' in contract.pricing_model)
        self.assertEquals(len(contract.pricing_model['single_payment']), 1)
        payment = contract.pricing_model['single_payment'][0]
        self.assertEquals(payment['label'], 'Price component update')
        self.assertEquals(payment['value'], '1.0')

        self.assertFalse('subscription' in contract.pricing_model)
        self.assertFalse('pay_per_use' in contract.pricing_model)

    def test_purchase_offering_update_exception(self):

        # Test view exceptions
        # Create the request, The user has not purchased a previous version
        # of the offering, so she is not allowed to purchase the offering
        data = {
            'offering': {
                'organization': 'test_organization',
                'name': 'test_offering',
                'version': '1.1'
            },
            'plan_label': 'update',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment': {
                'method': 'paypal'
            }
        }
        request = self.factory.post(
            '/api/contracting/',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        request.user = self._user
        purchase_collection = views.PurchaseCollection(permitted_methods=('POST',))

        response = purchase_collection.create(request)

        # Check response
        body_response = json.loads(response.content)
        self.assertEquals(body_response['result'], 'error')
        self.assertEquals(body_response['message'], 'Forbidden')
        self.assertEquals(response.status_code, 403)

        # Test Create contract exceptions

        offering = Offering.objects.get(pk="71000aba8e05ac2115f022ff")
        offering.offering_description = {
            'pricing': {
                'price_plans': [{
                    'title': 'Plan 1',
                    'label': 'update',
                    'price_components': []
                }, {
                    'title': 'Plan 1',
                    'label': 'regular',
                    'price_components': []
                }]
            }
        }

        offering.save()

        from datetime import datetime
        purchase = Purchase.objects.create(
            customer=self._user,
            date=datetime.now(),
            offering=offering,
            organization_owned=False,
            state='paid',
            tax_address={
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            bill=['/media/bills/11111111111.pdf']
        )
        from wstore.charging_engine.charging_engine import ChargingEngine

        # Check exceptions that can occur with multiple price plans when
        # creating the related purchase contract
        errors = {
            'The price plan label is required to identify the plan': None,
            'The specified plan does not exist': 'unexisting'
        }
        for err in errors:

            error = False
            msg = None
            try:
                charging = ChargingEngine(purchase, payment_method='paypal', plan=errors[err])
                charging._create_purchase_contract()
            except Exception, e:
                error = True
                msg = e.message

                self.assertTrue(error)
                self.assertEquals(msg, err)


class DeveloperPurchaseTestCase(TestCase):

    tags = ('fiware-ut-29',)
    fixtures = ('multiple_plan.json',)

    @classmethod
    def setUpClass(cls):
        cls._old_context = Context
        super(DeveloperPurchaseTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        Context = cls._old_context
        super(DeveloperPurchaseTestCase, cls).tearDownClass()

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        self._user = User.objects.get(username='test_user')

    def test_developer_offering_purchase(self):
        # Create the request
        data = {
            'offering': {
                'organization': 'test_organization',
                'name': 'test_offering',
                'version': '1.1'
            },
            'plan_label': 'developer',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment': {
                'method': 'paypal'
            }
        }
        request = self.factory.post(
            '/api/contracting/',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        request.user = self._user
        
        # Test purchase view
        views.create_purchase = MagicMock(name='create_purchase')
        offering = Offering.objects.get(pk="71000aba8e05ac2115f022ff")

        from datetime import datetime
        purchase = Purchase.objects.create(
            customer=self._user,
            date=datetime.now(),
            offering=offering,
            organization_owned=False,
            state='paid',
            tax_address={
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            bill=['/media/bills/22222222.pdf']
        )
        views.create_purchase.return_value = purchase

        views.get_current_site = MagicMock(name='get_current_site')
        views.get_current_site.return_value = Site.objects.get(name='antares')
        views.Context.objects.get = MagicMock(name='get')
        context = MagicMock()
        context.user_refs = []
        views.Context.objects.get.return_value = context

        purchase_collection = views.PurchaseCollection(permitted_methods=('POST',))

        response = purchase_collection.create(request)

        # Check response
        body_response = json.loads(response.content)
        self.assertEquals(len(body_response['bill']), 1)
        self.assertEquals(body_response['bill'][0], '/media/bills/22222222.pdf')
        payment_info = {
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment_method': 'paypal',
            'plan': 'developer',
            'accepted': False
        }
        views.create_purchase.assert_called_once_with(self._user, offering, org_owned=False, payment_info=payment_info)

    def test_developer_offering_purchase_exception(self):
        self._user.userprofile.get_current_roles = MagicMock()
        self._user.userprofile.get_current_roles.return_value = ['customer']

        # Create the request
        data = {
            'offering': {
                'organization': 'test_organization',
                'name': 'test_offering',
                'version': '1.1'
            },
            'plan_label': 'developer',
            'tax_address': {
                'street': 'test street',
                'postal': '28000',
                'city': 'test city',
                'country': 'test country'
            },
            'payment': {
                'method': 'paypal'
            }
        }
        request = self.factory.post(
            '/api/contracting/',
            json.dumps(data),
            HTTP_ACCEPT='application/json; charset=utf-8',
            content_type='application/json; charset=utf-8'
        )
        request.user = self._user
        purchase_collection = views.PurchaseCollection(permitted_methods=('POST',))

        response = purchase_collection.create(request)
        # Check response
        body_response = json.loads(response.content)
        self.assertEquals(body_response['result'], 'error')
        self.assertEquals(body_response['message'], 'Forbidden')
        self.assertEquals(response.status_code, 403)
