from __future__ import absolute_import

import os
import json
import subprocess
from datetime import datetime

from django.conf import settings
from django.template import loader, Context

from fiware_store.models import Resource
from fiware_store.models import UserProfile
from charging_engine.models import Contract
from charging_engine.models import Unit
from charging_engine.price_resolver import resolve_price
from store_commons.utils.usdlParser import USDLParser


class ChargingEngine:

    _sdr = None
    _price_model = None
    _purchase = None

    def __init__(self, purchase, sdr=None):
        self._purchase = purchase

    def _charge_client(self, price, concept):
        # Call payment gateway: TODO Fakepal
        # Update contract
        contract = self._purchase.contract
        contract.charges.append({
            'date': datetime.now(),
            'cost': price,
            'currency': 'euros',  # FIXME allow any currency
            'concept': concept
        })
        contract.last_charge = datetime.now()
        contract.save()

    def _generate_cdr(self, cost, tax):
        pass

    def _generate_invoice(self, price, applied_parts, type_):

        parts = []

        if type_ == 'initial':
            # If initial can only contain single payments and subscriptions
            if 'single_payment' in applied_parts:
                for part in applied_parts['single_payment']:
                    parts.append((part['title'], part['value'], part['unit'], part['currency']))

            if 'subscription' in applied_parts:
                for part in applied_parts['subscription']:
                    parts.append((part['title'], part['value'], part['unit'], part['currency']))

        elif type_ == 'renovation':
            # If renovation can only contain subscription
            for part in applied_parts['subscription']:
                parts.append((part['title'], part['value'], part['unit'], part['currency']))

        elif type_ == 'use':
            # If use can only contain pay per use parts
            for part in applied_parts['pay_per_use']:
                parts.append((part['title'], part['value'], part['unit'], part['currency']))

        # Get the bill template
        bill_template = loader.get_template('contracting/bill_template.html')

        tax = self._purchase.tax_address

        # Render the bill template
        offering = self._purchase.offering
        customer = self._purchase.customer

        customer_profile = UserProfile.objects.get(user=customer)

        resources = []
        for res in offering.resources:
            r = Resource.objects.get(pk=str(res))
            resources.append((r.name, r.description))

        date = str(self._purchase.contract.last_charge).split(' ')[0]
        # Load pricing info into the context
        context = {
            'BASEDIR': settings.BASEDIR,
            'offering_name': offering.name,
            'off_organization': offering.owner_organization,
            'off_version': offering.version,
            'ref': self._purchase.ref,
            'date': date,
            'organization': customer_profile.organization.name,
            'customer': customer_profile.complete_name,
            'address': tax.get('street'),
            'postal': tax.get('postal'),
            'city': tax.get('city'),
            'country': tax.get('country'),
            'parts': parts,
            'taxes': [],
            'subtotal': price,  # TODO price without taxes
            'tax': '0',
            'total': price,
            'resources': resources,
            'cur': 'euros'  # General currency of the invoice
        }

        bill_code = bill_template.render(Context(context))

        # Create the bill code file
        invoice_name = self._purchase.ref + '_' + date
        bill_path = os.path.join(settings.BILL_ROOT, invoice_name + '.html')
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
        self._purchase.bill.append(os.path.join(settings.MEDIA_URL, 'bills/' + invoice_name + '.pdf'))

        self._purchase.save()

    def _create_purchase_contract(self):
        # Generate the pricing model structure
        offering = self._purchase.offering
        parser = USDLParser(json.dumps(offering.offering_description), 'application/json')
        parsed_usdl = parser.parse()

        usdl_pricing = {}
        # Only a price plan is supported in this version
        if len(parsed_usdl['pricing']['price_plans']) > 0:
            usdl_pricing = parsed_usdl['pricing']['price_plans'][0]

        price_model = {}

        if 'price_components' in usdl_pricing:
            for comp in usdl_pricing['price_components']:

                try:
                    unit = Unit.objects.get(name=comp['unit'])
                except:
                    raise(Exception, 'Unsupported unit in price plan model')

                if unit.defined_model == 'single payment':
                    if not 'single_payment' in price_model:
                        price_model['single_payment'] = []

                    price_model['single_payment'].append(comp)

                elif unit.defined_model == 'subscription':
                    if not 'subscription' in price_model:
                        price_model['subscription'] = []

                    price_model['subscription'].append(comp)

                elif unit.defined_model == 'pay per use':
                    if not 'pay_per_use' in price_model:
                        price_model['pay_per_use'] = []

                    price_model['pay_per_use'].append(comp)

        # Create the contract entry
        Contract.objects.create(
            pricing_model=price_model,
            charges=[],
            applied_sdrs=[],
            purchase=self._purchase
        )
        self._price_model = price_model

    def resolve_charging(self, new_purchase=False):

        # Check if there is a new purchase
        if new_purchase:
            # Create the contract
            self._create_purchase_contract()
            charge = False
            related_model = {}

            # Check if there are price parts different from pay per use
            if 'single_payment' in self._price_model:
                charge = True
                related_model['single_payment'] = self._price_model['single_payment']

            if 'subscription' in self._price_model:
                charge = True
                related_model['subscription'] = self._price_model['subscription']

            price = 0
            if charge:
                # Call the price resolver
                price = resolve_price(related_model)
                # Make the charge
                self._charge_client(price, 'initial charge')

        #         Create the CDR
        #         Send the CDR to the RSS

            # Generate the invoice
            self._generate_invoice(price, related_model, 'initial')

        # If not new purchase get the price model from the contract entry
        # Check if there is a CDR is order to determine if it is a pay per use
        # charge or a Suscription renovation
        # Call the price resolver
        # Charge the client ??? Open issue: SDR periodicity
        # Generate the CDR
        # Sends the CDR to RSS
        # If charged generate the invoice
