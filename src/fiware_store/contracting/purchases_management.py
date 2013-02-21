import os
import subprocess
from datetime import datetime

from django.conf import settings
from django.template import loader, Context

from fiware_store.models import Purchase
from fiware_store.models import UserProfile
from fiware_store.models import Resource


def generate_bill(purchase):
    # Get the bill template
    bill_template = loader.get_template('contracting/bill_template.html')

    tax = purchase.tax_address

    # Render the bill template
    offering = purchase.offering
    customer = purchase.customer

    customer_profile = UserProfile.objects.get(user=customer)

    resources = []
    for res in offering.resources:
        r = Resource.objects.get(pk=str(res))
        resources.append((r.name, r.description))

    date = str(purchase.date).split(' ')[0]

    # Load pricing info into the context
    context = {
        'BASEDIR': settings.BASEDIR,
        'offering_name': offering.name,
        'off_organization': offering.owner_organization,
        'off_version': offering.version,
        'ref': purchase.pk,
        'date': date,
        'organization': customer_profile.organization.name,
        'customer': customer_profile.complete_name,
        'address': tax.get('street'),
        'postal': tax.get('postal'),
        'city': tax.get('city'),
        'country': tax.get('country'),
        'parts': [],
        'taxes': [],
        'subtotal': '0 Euros',
        'tax': '0',
        'total': '0 Euros',
        'resources': resources
    }

    bill_code = bill_template.render(Context(context))

    # Create the bill code file
    bill_path = os.path.join(settings.BILL_ROOT, purchase.pk + '.html')
    f = open(bill_path, 'wb')
    f.write(bill_code)
    f.close()
    # Compile the bill file
    subprocess.call(['/usr/bin/wkhtmltopdf', bill_path, bill_path[:-4] + 'pdf'])

    # Remove temporal files
    for file_ in os.listdir(settings.BILL_ROOT):

        if not file_.endswith('.pdf'):
            os.remove(os.path.join(settings.BILL_ROOT, file_))

    # Load bill path into the purchase
    purchase.bill = os.path.join(settings.MEDIA_URL, 'bills/' + purchase.pk + '.pdf')

    # Load ref field
    purchase.ref = purchase.pk
    purchase.save()


def create_purchase(user, offering, org_owned=False, tax_address=None):

    if offering.state != 'published':
        raise Exception("This offering can't be purchased")

    profile = UserProfile.objects.get(user=user)

    if offering.pk in profile.offerings_purchased or offering.pk in profile.organization.offerings_purchased:
        raise Exception('The offering has been already purchased')

    #Get the effective tax address
    if tax_address == None:
        tax = profile.tax_address
    else:
        tax = tax_address

    org = ''
    if org_owned == True:
        organization = profile.organization
        org = organization.name
        organization.purchased_offerings.append(offering.pk)

    # Create the purchase
    purchase = Purchase.objects.create(
        customer=user,
        date=datetime.now(),
        offering=offering,
        owner_organization=org,
        organization_owned=org_owned,
        state='paid',
        tax_address=tax
    )

    # Add the offering to the user profile
    profile.offerings_purchased.append(offering.pk)
    profile.save()

    return purchase
