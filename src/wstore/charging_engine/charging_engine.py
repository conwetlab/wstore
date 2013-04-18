from __future__ import absolute_import

import os
import json
import time
import subprocess
import threading
from pymongo import MongoClient
from bson import ObjectId

from datetime import datetime
from paypalpy import paypal

from django.conf import settings
from django.template import loader, Context
from django.contrib.sites.models import Site

from wstore.models import Resource
from wstore.models import UserProfile
from wstore.models import Purchase
from wstore.charging_engine.models import Contract
from wstore.charging_engine.models import Unit
from wstore.charging_engine.price_resolver import resolve_price
from wstore.store_commons.utils.usdlParser import USDLParser
from wstore.contracting.purchase_rollback import rollback


class ChargingEngine:

    _sdr = None
    _price_model = None
    _purchase = None
    _payment_method = None
    _credit_card_info = None

    def __init__(self, purchase, payment_method=None, credit_card=None, sdr=None):
        self._purchase = purchase
        if payment_method != None:

            if payment_method != 'paypal':
                if payment_method != 'credit_card':
                    raise Exception('Invalid payment method')
                else:
                    if credit_card == None:
                        raise Exception('No credit card provided')
                    self._credit_card_info = credit_card

            self._payment_method = payment_method

    def _timeout_handler(self):

        connection = MongoClient()
        db = connection[settings.DATABASES['default']['NAME']]

        # Uses an atomic operation to get and set the _lock value in the purchase
        # document
        pre_value = db.wstore_purchase.find_and_modify(
            query={'_id': ObjectId(self._purchase.pk)},
            update={ '$set': {'_lock': True}}
        )

        # If _lock not exists or is set to false means that this function has
        # acquired the resource
        if not '_lock' in pre_value or not pre_value['_lock']:

            # Only rollback if the state is pending
            if pre_value['state'] == 'pending':
                # Refresh the purchase
                purchase = Purchase.objects.get(pk=self._purchase.pk)
                rollback(purchase)

            db.wstore_purchase.find_and_modify(
                query={'_id': ObjectId(self._purchase.pk)},
                update={ '$set': {'_lock': False}}
            )

    def _fix_price(self, price):

        price = str(price)

        if price.find('.') != -1:
            splited_price = price.split('.')

            if len(splited_price[1]) > 2:
                price = splited_price[0] + '.' + splited_price[1][:2]
            elif len(splited_price[1]) < 2:
                price = price + '0'

        return price

    def _charge_client(self, price, concept):

        # Call payment gateway (paypal)
        # Configure paypal credentials
        paypal.SKIP_AMT_VALIDATION = True
        pp = paypal.PayPal(settings.PAYPAL_USER, settings.PAYPAL_PASSWD, settings.PAYPAL_SIGNATURE, settings.PAYPAL_URL)

        country_code = None
        # Get country code
        for cc in paypal.COUNTRY_CODES:
            if cc[1].lower() == self._purchase.tax_address['country'].lower():
                country_code = cc[0]
                break

        if country_code == None:
            raise Exception('Country not recognized')

        price = self._fix_price(price)

        if self._payment_method == 'credit_card':
            try:
                resp = pp.DoDirectPayment(
                    paymentaction='Sale',
                    ipaddress='192.168.1.1',
                    creditcardtype=self._credit_card_info['type'],
                    acct=self._credit_card_info['number'],
                    expdate=paypal.ShortDate(int(self._credit_card_info['expire_year']), int(self._credit_card_info['expire_month'])),
                    cvv2=self._credit_card_info['cvv2'],
                    firstname=self._purchase.customer.first_name,
                    lastname=self._purchase.customer.last_name,
                    street=self._purchase.tax_address['street'],
                    state='mad',
                    city=self._purchase.tax_address['city'],
                    countrycode=country_code,
                    zip=self._purchase.tax_address['postal'],
                    amt=price,
                    currencycode='EUR'
                )
            except Exception, e:
                raise Exception('Error while creating payment: ' + e.value)
            self._purchase.state = 'paid'

        elif self._payment_method == 'paypal':
            # Set express checkout
            url = Site.objects.all()[0].domain
            if url[-1] != '/':
                url += '/'

            try:
                resp = pp.SetExpressCheckout(
                    paymentrequest_0_paymentaction='Sale',
                    paymentrequest_0_amt=price,
                    paymentrequest_0_currencycode='EUR',
                    returnurl=url + 'api/contracting/' + self._purchase.ref + '/accept',
                    cancelurl=url + 'api/contracting/' + self._purchase.ref + '/cancel',
                )

                # Set timeout for PayPal transaction to 5 minutes
                t = threading.Timer(300, self._timeout_handler)
                t.start()

            except Exception, e:
                raise Exception('Error while creating payment: ' + e.value)

            return settings.PAYPAL_CHECKOUT_URL + '&token=' + resp['TOKEN'][0]
        else:
            raise Exception('Invalid payment method')

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

        last_charge = self._purchase.contract.last_charge

        if last_charge == None:
            # If last charge is None means that it is the invoice generation
            # associated with a free offering
            date = str(datetime.now()).split(' ')[0]
        else:
            date = str(last_charge).split(' ')[0]

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

    def _calculate_renovation_date(self, unit):

        renovation_date = None

        now = datetime.now()
        # Transform now date into seconds
        now = time.mktime(now.timetuple())

        if unit.lower() == 'per week':
            renovation_date = now + 604800  # 7 days
        elif unit.lower() == 'per month':
            renovation_date = now + 2592000  # 30 days
        elif unit.lower() == 'per year':
            renovation_date = now + 31536000  # 365 days
        else:
            raise Exception('Invalid unit')

        renovation_date = datetime.fromtimestamp(renovation_date)
        return renovation_date

    def end_charging(self, price, concept, related_model):

        # Update purchase state
        if self._purchase.state == 'pending':
            self._purchase.state = 'paid'
            self._purchase.save()

        # Update contract
        contract = self._purchase.contract
        contract.charges.append({
            'date': datetime.now(),
            'cost': price,
            'currency': 'euros',  # FIXME allow any currency
            'concept': concept
        })

        contract.pending_payment = {}
        if self._price_model == None:
            self._price_model = contract.pricing_model

        contract.last_charge = datetime.now()

        if concept == 'initial charge':
            # If subscription parts has been charged update renovation dates
            if 'subscription' in related_model:
                updated_subscriptions = []

                for subs in self._price_model['subscription']:
                    up_sub = subs
                    # Calculate renovation date
                    up_sub['renovation_date'] = self._calculate_renovation_date(subs['unit'])
                    updated_subscriptions.append(subs)

                    self._price_model['subscription'] = updated_subscriptions

                # Update price model in contract
                contract.pricing_model = self._price_model
                # Create the CDR
                # Send the CDR to the RSS

            # Generate the invoice
            self._generate_invoice(price, related_model, 'initial')

        elif concept == 'Renovation':

            for subs in related_model['subscription']:
                subs['renovation_date'] = self._calculate_renovation_date(subs['unit'])

            updated_subscriptions = related_model['subscription']
            if 'unmodified' in related_model:
                updated_subscriptions.extend(related_model['unmodified'])

            self._price_model['subscription'] = updated_subscriptions
            contract.pricing_model = self._price_model
            self._generate_invoice(price, related_model, 'Renovation')

        contract.save()

    def resolve_charging(self, new_purchase=False, sdr=None):

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
                redirect_url = self._charge_client(price, 'initial charge')

            if self._purchase.state == 'paid':
                self.end_charging(price, 'initial charge', related_model)
            else:
                price = self._fix_price(price)
                self._purchase.contract.pending_payment = {
                    'price': price,
                    'concept': 'initial charge',
                    'related_model': related_model
                }
                self._purchase.contract.save()
                return redirect_url

        else:
            self._price_model = self._purchase.contract.pricing_model
            self._purchase.state = 'pending'
            self._purchase.save()

            # If not SDR received means that the call is a renovation
            if sdr == None:
                # Determine the price parts to renovate
                if not 'subscription' in self._price_model:
                    raise Exception('No subscriptions to renovate')

                related_model = {
                    'subscription': []
                }

                now = datetime.now()
                unmodified = []

                for s in self._price_model['subscription']:
                    renovation_date = s['renovation_date']

                    if renovation_date < now:
                        related_model['subscription'].append(s)
                    else:
                        unmodified.append(s)

                price = resolve_price(related_model)
                redirect_url = self._charge_client(price, 'Renovation')

                if len(unmodified) > 0:
                    related_model['unmodified'] = unmodified

                if self._purchase.state == 'paid':
                    self.end_charging(price, 'Renovation', related_model)
                else:
                    price = self._fix_price(price)
                    self._purchase.contract.pending_payment = {
                        'price': price,
                        'concept': 'Renovation',
                        'related_model': related_model
                    }
                    self._purchase.contract.save()
                    return redirect_url
