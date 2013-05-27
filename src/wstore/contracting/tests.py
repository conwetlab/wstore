from django.test import TestCase
from django.contrib.auth.models import User

from wstore.contracting import purchases_management
from wstore.contracting.purchase_rollback import rollback
from wstore.models import Offering
from wstore.models import Organization
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.charging_engine.models import Contract


class FakeChargingEngine:

    def __init__(self, purchase, payment_method=None, credit_card=None):
        pass

    def resolve_charging(self, new_purchase):
        pass


def fake_generate_bill():
    pass


class PurchasesCreationTestCase(TestCase):

    fixtures = ['purch_creat.json']

    @classmethod
    def setUpClass(cls):
        purchases_management.generate_bill = fake_generate_bill
        purchases_management.ChargingEngine = FakeChargingEngine
        super(PurchasesCreationTestCase, cls).setUpClass()

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

        purchase = purchases_management.create_purchase(user, offering, True, payment_info=payment_info)

        self.assertEqual(purchase.customer.username, 'test_user')
        self.assertEqual(purchase.organization_owned, True)
        self.assertEqual(purchase.owner_organization, 'test_organization')
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

    def test_purchase_already_purchased_org(self):

        user = User.objects.get(username='test_user')
        offering = Offering.objects.get(name='test_offering3')
        user_profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        org.offerings_purchased = ['81000aba8e05ac2115f022f0']
        org.save()
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
