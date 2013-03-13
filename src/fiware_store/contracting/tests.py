from django.test import TestCase
from django.contrib.auth.models import User

from fiware_store.contracting import purchases_management
from fiware_store.models import Offering
from fiware_store.models import Organization
from fiware_store.models import Purchase
from fiware_store.models import UserProfile


class FakeChargingEngine:

    def __init__(self, purchase):
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

        purchase = purchases_management.create_purchase(user, offering)

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
        user_profile.tax_address = tax_address
        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()
        purchase = purchases_management.create_purchase(user, offering, True)

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

        tax_address = {
            'street': 'test street',
            'postal': '28000',
            'city': 'test city',
            'country': 'test country'
        }

        user_profile = UserProfile.objects.get(user=user)
        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        purchase = purchases_management.create_purchase(user, offering, tax_address=tax_address)

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

        tax_address = {
            'street': 'test street',
            'postal': '28000',
            'city': 'test city',
            'country': 'test country'
        }

        error = False
        msg = None

        try:
            purchases_management.create_purchase(user, offering, tax_address=tax_address)
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

        tax_address = {
            'street': 'test street',
            'postal': '28000',
            'city': 'test city',
            'country': 'test country'
        }

        error = False
        msg = None

        try:
            purchases_management.create_purchase(user, offering, tax_address=tax_address)
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

        tax_address = {
            'street': 'test street',
            'postal': '28000',
            'city': 'test city',
            'country': 'test country'
        }

        error = False
        msg = None

        try:
            purchases_management.create_purchase(user, offering, tax_address=tax_address)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, "The offering has been already purchased")
