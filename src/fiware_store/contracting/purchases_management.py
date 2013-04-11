from datetime import datetime

from fiware_store.charging_engine.charging_engine import ChargingEngine
from fiware_store.models import Purchase
from fiware_store.models import UserProfile
from fiware_store import charging_engine


def create_purchase(user, offering, org_owned=False, payment_info=None):

    if offering.state != 'published':
        raise Exception("This offering can't be purchased")

    profile = UserProfile.objects.get(user=user)

    if offering.pk in profile.offerings_purchased or offering.pk in profile.organization.offerings_purchased:
        raise Exception('The offering has been already purchased')

    #Get the effective tax address
    if not 'tax_address' in payment_info:
        tax = profile.tax_address
    else:
        tax = payment_info['tax_address']

    # Check the payment method before purchase creation in order to avoid
    # an inconsistent state in the database
    credit_card_info = None
    if payment_info['payment_method'] == 'credit_card':
        if 'number' in payment_info['credit_card']:
            credit_card_info = payment_info['credit_card']
        else:
            credit_card_info = profile.payment_info['credit_card']
            credit_card_info['cvv2'] = payment_info['credit_card']['cvv2']

    elif payment_info['payment_method'] != 'paypal':
        raise Exception('Invalid payment method')

    org = ''
    if org_owned == True:
        organization = profile.organization
        org = organization.name
        organization.offerings_purchased.append(offering.pk)
        organization.save()

    # Create the purchase
    purchase = Purchase.objects.create(
        customer=user,
        date=datetime.now(),
        offering=offering,
        owner_organization=org,
        organization_owned=org_owned,
        state='pending',
        tax_address=tax
    )
    # Load ref
    purchase.ref = purchase.pk
    purchase.save()

    # Add the offering to the user profile
    profile.offerings_purchased.append(offering.pk)
    profile.save()

    if credit_card_info != None:
        charging_engine = ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card_info)
    else:
        charging_engine = ChargingEngine(purchase, payment_method='paypal')

    redirect_url = charging_engine.resolve_charging(new_purchase=True)

    if redirect_url == None:
        result = purchase
    else:
        result = redirect_url

    return result
