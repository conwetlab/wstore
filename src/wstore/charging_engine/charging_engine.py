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
from django.contrib.auth.models import User

from wstore.models import Resource
from wstore.models import UserProfile
from wstore.models import Purchase
from wstore.models import Offering
from wstore.models import RSS
from wstore.charging_engine.models import Contract
from wstore.charging_engine.models import Unit
from wstore.charging_engine.price_resolver import resolve_price
from wstore.store_commons.utils.usdlParser import USDLParser
from wstore.contracting.purchase_rollback import rollback
from wstore.rss_adaptor.rssAdaptor import RSSAdaptor
from wstore.rss_adaptor.utils.rss_codes import get_country_code, get_curency_code


class ChargingEngine:

    _price_model = None
    _purchase = None
    _payment_method = None
    _credit_card_info = None

    def __init__(self, purchase, payment_method=None, credit_card=None):
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
            update={'$set': {'_lock': True}}
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
                update={'$set': {'_lock': False}}
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

    def _get_country_code(self, country):

        country_code = None
        # Get country code
        for cc in paypal.COUNTRY_CODES:
            if cc[1].lower() == country.lower():
                country_code = cc[0]
                break

        return country_code

    def _charge_client(self, price, concept):

        # Call payment gateway (paypal)
        # Configure paypal credentials
        paypal.SKIP_AMT_VALIDATION = True
        pp = paypal.PayPal(settings.PAYPAL_USER, settings.PAYPAL_PASSWD, settings.PAYPAL_SIGNATURE, settings.PAYPAL_URL)

        country_code = self._get_country_code(self._purchase.tax_address['country'])

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
                raise Exception('Error while creating payment: ' + e.value[0])
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
                raise Exception('Error while creating payment: ' + e.value[0])

            return settings.PAYPAL_CHECKOUT_URL + '&token=' + resp['TOKEN'][0]
        else:
            raise Exception('Invalid payment method')

    def _generate_cdr(self, applied_parts, time_stamp):

        cdrs = []

        # Take the first RSS registered
        rss = RSS.objects.all()[0]

        # Create connection for raw database access
        connection = MongoClient()
        db = connection[settings.DATABASES['default']['NAME']]

        # Get the service name using direct access to the stored
        # JSON USDL description

        offering_description = self._purchase.offering.offering_description

        # Get the used tag for RDF properties
        service_tag = ''
        dc_tag = ''
        for k, v in offering_description['@context'].iteritems():
            if v == 'http://www.linked-usdl.org/ns/usdl-core#':
                service_tag = k
            if v == 'http://purl.org/dc/terms/':
                dc_tag = k

        # Get the service name
        service_name = ''
        for node in offering_description['@graph']:
            if node['@type'] == service_tag + ':Service':
                service_name = node[dc_tag + ':title']['@value']

        # Get the provider (Organization)
        provider = self._purchase.offering.owner_organization

        # Set offering ID
        offering = self._purchase.offering.name + ' ' + self._purchase.offering.version

        # Get the customer
        if self._purchase.organization_owned:
            customer = self._purchase.owner_organization
        else:
            customer = self._purchase.customer.username

        # Get the country code
        country_code = self._get_country_code(self._purchase.tax_address['country'])
        country_code = get_country_code(country_code)

        # Check the type of the applied parts
        if 'single_payment' in applied_parts:

            # A cdr is generated for every price part
            for part in applied_parts['single_payment']:

                # Take and increment the correlation number using
                # the mongoDB atomic access in order to avoid race
                # problems
                corr_number = db.wstore_rss.find_and_modify(
                    query={'_id': ObjectId(rss.pk)},
                    update={'$inc': {'correlation_number': 1}}
                )['correlation_number']

                # Set the description
                description = 'Single payment: ' + part['value'] + ' ' + part['currency']
                currency = get_curency_code(part['currency'])

                cdrs.append({
                    'provider': provider,
                    'service': service_name,
                    'defined_model': 'Single payment event',
                    'correlation': str(corr_number),
                    'purchase': self._purchase.pk,
                    'offering': offering,
                    'product_class': 'SaaS',
                    'description': description,
                    'cost_currency': currency,
                    'cost_value': part['value'],
                    'tax_currency': '1',
                    'tax_value': '0.0',
                    'source': '1',
                    'operator': '1',
                    'country': country_code,
                    'time_stamp': time_stamp,
                    'customer': customer,
                })

        if 'subscription' in applied_parts:

            # A cdr is generated by price part
            for part in applied_parts['subscription']:

                corr_number = db.wstore_rss.find_and_modify(
                    query={'_id': ObjectId(rss.pk)},
                    update={'$inc': {'correlation_number': 1}}
                )['correlation_number']

                # Set the description
                description = 'Subscription: ' + part['value'] + ' ' + part['currency'] + ' ' + part['unit']
                currency = get_curency_code(part['currency'])

                cdrs.append({
                    'provider': provider,
                    'service': service_name,
                    'defined_model': 'Subscription event',
                    'correlation': str(corr_number),
                    'purchase': self._purchase.pk,
                    'offering': offering,
                    'product_class': 'SaaS',
                    'description': description,
                    'cost_currency': currency,
                    'cost_value': part['value'],
                    'tax_currency': '1',
                    'tax_value': '0.0',
                    'source': '1',
                    'operator': '1',
                    'country': country_code,
                    'time_stamp': time_stamp,
                    'customer': customer,
                })

        if 'pay_per_use' in applied_parts:

            # A cdr is generated by price part
            for part in applied_parts['pay_per_use']:

                corr_number = db.wstore_rss.find_and_modify(
                    query={'_id': ObjectId(rss.pk)},
                    update={'$inc': {'correlation_number': 1}}
                )['correlation_number']

                # Set the description
                description = 'Fee per ' + part['unit'] + ', Consumption: ' + part['value']
                currency = get_curency_code(part['applied_part']['currency'])

                cdrs.append({
                    'provider': provider,
                    'service': service_name,
                    'defined_model': 'Pay per use event',
                    'correlation': str(corr_number),
                    'purchase': self._purchase.pk,
                    'offering': offering,
                    'product_class': 'SaaS',
                    'description': description,
                    'cost_currency': currency,
                    'cost_value': part['price'],
                    'tax_currency': 'EUR',
                    'tax_value': '0.0',
                    'source': '1',
                    'operator': '1',
                    'country': country_code,
                    'time_stamp': time_stamp,
                    'customer': customer,
                })

        # Send the created CDRs to the Revenue Sharing System
        rss_adaptor = RSSAdaptor(rss.host)
        rss_adaptor.send_cdr(cdrs)

    def _generate_invoice(self, price, applied_parts, type_):

        parts = []

        if type_ == 'initial':
            # If initial can only contain single payments and subscriptions
            parts = {
                'single_parts': [],
                'subs_parts': []
            }
            if 'single_payment' in applied_parts:
                for part in applied_parts['single_payment']:
                    parts['single_parts'].append((part['title'], part['value'], part['currency']))

            if 'subscription' in applied_parts:
                for part in applied_parts['subscription']:
                    parts['subs_parts'].append((part['title'], part['value'], part['currency'], part['unit'], str(part['renovation_date'])))

            # Get the bill template
            bill_template = loader.get_template('contracting/bill_template_initial.html')

        elif type_ == 'renovation':
            # If renovation can only contain subscription
            for part in applied_parts['subscription']:
                parts.append((part['title'], part['value'], part['currency'], part['unit'], str(part['renovation_date'])))

            # Get the bill template
            bill_template = loader.get_template('contracting/bill_template_renovation.html')

        elif type_ == 'use':
            # If use can only contain pay per use parts
            for part in applied_parts['pay_per_use']:
                parts.append((part['applied_part']['title'], part['applied_part']['value'],
                              part['applied_part']['currency'], part['applied_part']['unit'],
                              part['value'], part['price']))

            # Get the bill template
            bill_template = loader.get_template('contracting/bill_template_use.html')

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
            'taxes': [],
            'subtotal': price,  # TODO price without taxes
            'tax': '0',
            'total': price,
            'resources': resources,
            'cur': 'euros'  # General currency of the invoice
        }

        # Include the corresponding parts
        if type_ == 'initial':
            context['exists_single'] = False
            context['exists_subs'] = False

            if len(parts['single_parts']) > 0:
                context['single_parts'] = parts['single_parts']
                context['exists_single'] = True

            if len(parts['subs_parts']) > 0:
                context['subs_parts'] = parts['subs_parts']
                context['exists_subs'] = True
        else:
            context['parts'] = parts

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

    def include_sdr(self, sdr):
        # Check the offering and customer
        off_data = sdr['offering']
        offering = Offering.objects.get(name=off_data['name'], owner_organization=off_data['organization'], version=off_data['version'])

        if offering != self._purchase.offering:
            raise Exception('The offering defined in the SDR is not the purchase offering')

        customer = User.objects.get(username=sdr['customer'])

        if self._purchase.organization_owned:
            # Check if the user belongs to the organization
            profile = UserProfile.objects.get(user=customer)
            if profile.organization.name != self._purchase.owner_organization:
                raise Exception('The user not belongs to the owner organization')
        else:
            # Check if the user has purchased the offering
            if customer != self._purchase.customer:
                raise Exception('The user has not purchased the offering')

        # Extract the pricing model from the purchase
        self._price_model = self._purchase.contract.pricing_model

        if not 'pay_per_use' in self._price_model:
            raise Exception('No pay per use parts in the pricing model of the offering')

        # Check the correlation number and timestamp
        applied_sdrs = self._purchase.contract.applied_sdrs
        pending_sdrs = self._purchase.contract.pending_sdrs
        last_corr = 0
        last_time = 0

        if len(pending_sdrs) > 0:
            last_corr = int(pending_sdrs[-1]['correlation_number'])
            last_time = pending_sdrs[-1]['time_stamp']
            last_time = time.mktime(last_time.timetuple())
        else:
            if len(applied_sdrs) > 0:
                last_corr = int(applied_sdrs[-1]['correlation_number'])
                last_time = applied_sdrs[-1]['time_stamp']
                last_time = time.mktime(last_time.timetuple())

        time_stamp = datetime.strptime(sdr['time_stamp'], '%Y-%m-%d %H:%M:%S.%f')
        time_stamp_sec = time.mktime(time_stamp.timetuple())

        if (int(sdr['correlation_number']) != last_corr + 1):
            raise Exception('Invalid correlation number, expected: ' + str(last_corr + 1))

        if last_time > time_stamp_sec:
            raise Exception('Invalid time stamp')

        related_model = {
            'pay_per_use': self._price_model['pay_per_use']
        }

        # Call the price resolver
        price_resolved = resolve_price(related_model, sdr)

        # Store the SDR and the related price
        sdr['time_stamp'] = time_stamp
        sdr['price'] = price_resolved['price']
        sdr['applied_part'] = price_resolved['part']

        self._purchase.contract.pending_sdrs.append(sdr)
        self._purchase.contract.save()

    def end_charging(self, price, concept, related_model):

        # Update purchase state
        if self._purchase.state == 'pending':
            self._purchase.state = 'paid'
            self._purchase.save()

        # Update contract
        contract = self._purchase.contract

        time_stamp = datetime.now()

        if price > 0:
            contract.charges.append({
                'date': time_stamp,
                'cost': price,
                'currency': 'EUR',  # FIXME allow any currency
                'concept': concept
            })

        contract.pending_payment = {}
        if self._price_model == None:
            self._price_model = contract.pricing_model

        contract.last_charge = time_stamp

        if concept == 'initial charge':
            # If subscription parts has been charged update renovation dates
            if 'subscription' in related_model:
                updated_subscriptions = []

                for subs in self._price_model['subscription']:
                    up_sub = subs
                    # Calculate renovation date
                    up_sub['renovation_date'] = self._calculate_renovation_date(subs['unit'])
                    updated_subscriptions.append(up_sub)

                self._price_model['subscription'] = updated_subscriptions

                # Update price model in contract
                contract.pricing_model = self._price_model
                related_model['subscription'] = updated_subscriptions

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
            related_model['subscription'] = updated_subscriptions
            self._generate_invoice(price, related_model, 'renovation')

        elif concept == 'pay per use':
            # Move SDR from pending to applied
            contract.applied_sdrs.extend(contract.pending_sdrs)
            contract.pending_sdrs = []
            # Generate the invoice
            self._generate_invoice(price, related_model, 'use')

        # The contract is saved before the CDR creation to prevent
        # that a transmission error in RSS request causes the
        # customer being charged twice
        contract.save()

        # If the customer has been charged create the CDR
        if price > 0:
            self._generate_cdr(related_model, str(time_stamp))

    def resolve_charging(self, new_purchase=False, sdr=False):

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
            else:
                # If it is not necessary to charge the customer the state is set to paid
                self._purchase.state = 'paid'

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
            if not sdr:
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

            # If sdr is true means that the call is a request for charging the use
            # made of a service.
            else:
                # Aggregate the calculated charges
                pending_sdrs = self._purchase.contract.pending_sdrs

                if len(pending_sdrs) == 0:
                    raise Exception('No SDRs to charge')

                related_model = {
                    'pay_per_use': [],
                }

                price = 0
                for pend_sdr in pending_sdrs:
                    price = price + pend_sdr['price']
                    # Construct the related model using SDR
                    related_model['pay_per_use'].append(pend_sdr)

                # Charge the client
                redirect_url = self._charge_client(price, 'Pay per use')

                if self._purchase.state == 'paid':
                    self.end_charging(price, 'pay per use', related_model)
                else:
                    price = self._fix_price(price)
                    self._purchase.contract.pending_payment = {
                        'price': price,
                        'concept': 'pay per use',
                        'related_model': related_model
                    }
                    self._purchase.contract.save()
                    return redirect_url
