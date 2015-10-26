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
from urlparse import urlunparse, urlparse

from django.contrib.sites.models import get_current_site
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_response, get_content_type, supported_request_mime_types, \
authentication_required
from wstore.store_commons.utils.version import is_lower_version
from wstore.offerings.offerings_management import get_offering_info
from wstore.contracting.purchases_management import create_purchase
from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.models import Offering, Organization, Context
from wstore.models import Purchase
from wstore.models import Resource as store_resource
from wstore.contracting.purchase_rollback import rollback


class PurchaseFormCollection(Resource):

    @authentication_required
    @supported_request_mime_types(('application/json', ))
    def create(self, request):

        data = json.loads(request.raw_post_data)

        # Get the offering
        try:
            if isinstance(data['offering'], dict):
                id_ = data['offering']
                org = Organization.objects.get(name=id_['organization'])
                offering = Offering.objects.get(owner_organization=org, name=id_['name'], version=id_['version'])
            else:
                offering = Offering.objects.get(description_url=data['offering'])
        except:
            return build_response(request, 404, 'Not found')

        redirect_uri = data['redirect_uri']

        # Check that the offering can be purchased
        if offering.state != 'published':
            return build_response(request, 400, 'The offering cannot be purchased')

        token = offering.pk + request.user.pk
        site = get_current_site(request)

        context = Context.objects.get(site=site)
        context.user_refs[token] = {
            'user': request.user.pk,
            'offering': offering.pk,
            'redirect_uri': redirect_uri
        }

        context.save()
        site = urlparse(site.domain)
        query = 'ID=' + token

        # Create the URL that shows the purchase form
        url = urlunparse((site[0], site[1], '/api/contracting/form', '', query, ''))

        response = {
            'url': url
        }

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @method_decorator(login_required)
    def read(self, request):

        # Get the token
        token = request.GET.get('ID', '')

        site = get_current_site(request)
        context = Context.objects.get(site=site)

        if token not in context.user_refs:
            return render(request, 'err_msg.html', {
                'title': 'Token not found',
                'message': 'The token provided for identifying the purchase is not valid or has expired.'
            })

        info = context.user_refs[token]

        # Get the user and the offering
        user = User.objects.get(pk=info['user'])
        request.user = user

        id_ = info['offering']

        context.save()

        # Load the offering info
        try:
            offering = Offering.objects.get(pk=id_)
        except:
            return render(request, 'err_msg.html', {
                'title': 'Offering not found',
                'message': 'The requested offering does not exists.'
            })

        offering_info = get_offering_info(offering, user)

        # Check that the offering can be purchased
        if offering.state != 'published':
            return render(request, 'err_msg.html', {
                'title': 'Error',
                'message': 'The offering cannot be acquired'
            })

        from django.conf import settings

        # Create the context
        context = {
            'offering_info': mark_safe(json.dumps(offering_info)),
            'oil': settings.OILAUTH,
            'portal': settings.PORTALINSTANCE
        }

        # Return the form to purchase the offering
        return render(request, 'store/purchase_form.html', context)


class PurchaseCollection(Resource):

    # Creates a new purchase resource
    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        user = request.user
        content_type = get_content_type(request)[0]

        try:
            data = json.loads(request.raw_post_data)
            payment_info = {}

            if isinstance(data['offering'], dict):
                id_ = data['offering']
                org = Organization.objects.get(name=id_['organization'])
                offering = Offering.objects.get(owner_organization=org, name=id_['name'], version=id_['version'])
            else:
                offering = Offering.objects.get(description_url=data['offering'])

            if 'tax_address' in data:
                payment_info['tax_address'] = data['tax_address']

            payment_info['payment_method'] = data['payment']['method']

            if 'credit_card' in data['payment']:
                payment_info['credit_card'] = data['payment']['credit_card']

            # Get terms and conditions flag
            payment_info['accepted'] = data.get('conditions_accepted', False)

            # Check the selected price plan
            update_plan = False
            developer_plan = False
            if 'plan_label' in data:
                payment_info['plan'] = data['plan_label']
                # Classify the plan
                # Check if the plan is an update
                if data['plan_label'].lower() == 'update':
                    update_plan = True

                # Check if the plan is a developer purchase
                elif data['plan_label'].lower() == 'developer':
                    developer_plan = True

            # Check if the user is purchasing for an organization

            org_owned = True
            if user.userprofile.is_user_org():
                org_owned = False

            # Check if the user has the customer role for the organization
            roles = user.userprofile.get_current_roles()
            if org_owned:

                if not 'customer' in roles and not developer_plan:
                    return build_response(request, 403, 'Forbidden')

                # Load the purchased offerings if it is an update in
                # order to check versions later
                if update_plan:
                    purchased_offerings = user.userprofile.current_organization.offerings_purchased

            elif update_plan:
                purchased_offerings = user.userprofile.offerings_purchased
                    
            # Check if the plan is an update
            if update_plan:
                # Check if the user has purchased a previous version
                found = False
                offerings = Offering.objects.filter(owner_organization=offering.owner_organization, name=offering.name)

                for off in offerings:
                    if off.pk in purchased_offerings and is_lower_version(off.version, offering.version):
                        found = True
                        break

                if not found:
                    return build_response(request, 403, 'Forbidden')

            if developer_plan and not 'developer' in roles:
                    return build_response(request, 403, 'Forbidden')

            response_info = create_purchase(user, offering, org_owned=org_owned, payment_info=payment_info)
        except Exception as e:
            # Check if the offering has been paid before the exception has been raised
            paid = False

            if org_owned:
                if offering.pk in request.user.userprofile.current_organization.offerings_purchased:
                    paid = True
                    response_info = Purchase.objects.get(owner_organization=request.user.userprofile.current_organization, offering=offering)
            else:
                if offering.pk in request.user.userprofile.offerings_purchased:
                    paid = True
                    response_info = Purchase.objects.get(customer=request.user, offering=offering, organization_owned=False)

            if not paid:
                return build_response(request, 400, unicode(e))

        response = {}
        # If the value returned by the create_purchase method is a string means that
        # the purchase is not ended and need user confirmation. response_info contains
        # the URL where redirect the user
        if isinstance(response_info, str) or isinstance(response_info, unicode):
            response['redirection_link'] = response_info
            status = 200
        else:  # The purchase is finished so the download links are returned
            # Load download resources URL

            response['resources'] = []

            for res in offering.resources:
                r = store_resource.objects.get(pk=res)

                # Check if the resource has been uploaded to the store or if is
                # in an external applications server
                if r.resource_path != '':
                    response['resources'].append(r.resource_path)
                elif r.download_link != '':
                    response['resources'].append(r.download_link)

            # Load bill URL
            response['bill'] = response_info.bill
            status = 201

        # Check if it is needed to redirect the user
        token = offering.pk + user.pk

        site = get_current_site(request)
        context = Context.objects.get(site=site)

        if token in context.user_refs:
            redirect_uri = context.user_refs[token]['redirect_uri']
            del(context.user_refs[token])
            context.save()
            response['client_redirection_uri'] = redirect_uri

        return HttpResponse(json.dumps(response), status=status, mimetype=content_type)


class PurchaseEntry(Resource):

    @authentication_required
    def read(self, request):
        pass

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, reference):

        purchase = Purchase.objects.get(ref=reference)

        data = json.loads(request.raw_post_data)

        try:
            if data['method'] == 'paypal':
                charging_engine = ChargingEngine(purchase, payment_method='paypal')
            elif data['method'] == 'credit_card':

                # Get the payment info
                if 'credit_card' in data:
                    credit_card = data['credit_card']
                else:
                    if purchase.organization_owned:
                        credit_card = purchase.owner_organization.payment_info
                    else:
                        credit_card = purchase.customer.userprofile.payment_info
                charging_engine = ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)

            charging_engine.resolve_charging(type_='renovation')
        except:
            # Refresh the purchase info
            purchase = Purchase.objects.get(ref=reference)
            rollback(purchase)
            return build_response(request, 400, 'Invalid JSON content')

        return build_response(request, 200, 'OK')
