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

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from wstore.store_commons.utils.http import build_response, supported_request_mime_types, \
authentication_required
from wstore.store_commons.resource import Resource
from wstore.models import UserProfile
from wstore.models import Organization
from wstore.models import Purchase
from wstore.charging_engine.models import Unit
from django.contrib.auth.decorators import login_required


def is_hidden_credit_card(number, profile_card):

    hidden = False
    if number.startswith('xxxxxxxxxxxx'):
        if number[12:] == profile_card[12:]:
            hidden = True

    return hidden


def is_valid_credit_card(number):
    valid = True
    digits = '1234567890'

    if len(number) != 16:
        valid = False

    for d in number:
        if not d in digits:
            valid = False

    return valid


class UserProfileCollection(Resource):

    @authentication_required
    def read(self, request):

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        response = []
        for user in User.objects.all():

            profile = UserProfile.objects.get(user=user)
            user_profile = {}
            user_profile['username'] = user.username
            user_profile['complete_name'] = profile.complete_name

            if not settings.OILAUTH:
                user_profile['first_name'] = user.first_name
                user_profile['last_name'] = user.last_name
                user_org = Organization.objects.get(name=user.username)
            else:
                user_org = Organization.objects.get(actor_id=profile.actor_id)

            user_profile['current_organization'] = profile.current_organization.name

            # Include user notification URL
            user_profile['notification_url'] = user_org.notification_url

            # Append organizations
            user_profile['organizations'] = []

            # Include organizations info
            for o in profile.organizations:
                org = Organization.objects.get(pk=o['organization'])

                org_info = {
                    'name': org.name,
                    'roles': o['roles']
                }

                if 'provider' in o['roles']:
                    org_info['notification_url'] = org.notification_url

                user_profile['organizations'].append(org_info)

            user_profile['tax_address'] = profile.tax_address

            # Include user roles
            user_profile['roles'] = profile.get_user_roles()

            if user.is_staff:
                user_profile['roles'].append('admin')

            if 'number' in profile.payment_info:
                user_profile['payment_info'] = {}
                number = profile.payment_info['number']
                number = 'xxxxxxxxxxxx' + number[-4:]
                user_profile['payment_info']['number'] = number
                user_profile['payment_info']['type'] = profile.payment_info['type']
                user_profile['payment_info']['expire_year'] = profile.payment_info['expire_year']
                user_profile['payment_info']['expire_month'] = profile.payment_info['expire_month']
                user_profile['payment_info']['cvv2'] = profile.payment_info['cvv2']

            response.append(user_profile)
        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        if settings.OILAUTH:
            return build_response(request, 403, 'It is not possible to create users (use Account enabler instead)')

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)

        # Validate Info
        if (not 'roles' in data) or (not 'username' in data) or (not 'first_name') in data \
        or (not 'last_name' in data) or (not 'password' in data):
            return build_response(request, 400, 'Missing required field')

        # Create the user
        try:
            user = User.objects.create(username=data['username'], first_name=data['first_name'], last_name=data['last_name'])

            # Create the password
            user.set_password(data['password'])

            if 'admin' in data['roles']:
                user.is_staff = True

            user.save()

            # Get the user profile
            user_profile = UserProfile.objects.get(user=user)
            user_profile.complete_name = data['first_name'] + ' ' + data['last_name']

            if 'notification_url' in data:
                user_profile.current_organization.notification_url = data['notification_url']
                user_profile.current_organization.save()

            if 'provider' in data['roles']:
                # Append the provider role to the user organization
                # The user profile is just created so only the private organization exists

                org = user_profile.organizations[0]
                org['roles'].append('provider')
                user_profile.save()
                user_profile.organizations = [org]

            if 'tax_address' in data:
                user_profile.tax_address = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'country': data['tax_address']['country']
                }
            if 'payment_info' in data:
                if not is_valid_credit_card(data['payment_info']['number']):
                    raise Exception()

                user_profile.payment_info = {
                    'type': data['payment_info']['type'],
                    'number': data['payment_info']['number'],
                    'expire_month': data['payment_info']['expire_month'],
                    'expire_year': data['payment_info']['expire_year'],
                    'cvv2': data['payment_info']['cvv2']
                }

            user_profile.save()

        except:
            return build_response(request, 400, 'Invalid content')

        return build_response(request, 201, 'Created')


class UserProfileEntry(Resource):

    @authentication_required
    def read(self, request, username):

        if not request.user.is_staff and not request.user.username == username:
            return build_response(request, 403, 'Forbidden')

        # Get user info
        user = User.objects.get(username=username)
        profile = UserProfile.objects.get(user=user)

        user_profile = {}
        user_profile['username'] = user.username
        user_profile['complete_name'] = profile.complete_name

        if not settings.OILAUTH:
            user_profile['first_name'] = user.first_name
            user_profile['last_name'] = user.last_name
            user_org = Organization.objects.get(name=user.username)
        else:
            user_org = Organization.objects.get(actor_id=profile.actor_id)

        # Include user organizations info
        user_profile['current_organization'] = profile.current_organization.name
        user_profile['organizations'] = []

        # Include notification URL for the user
        
        user_profile['notification_url'] = user_org.notification_url

        # Include organizations name
        for o in profile.organizations:
            org = Organization.objects.get(pk=o['organization'])

            org_info = {
                'name': org.name,
                'roles': o['roles']
            }

            if 'provider' in o['roles']:
                org_info['notification_url'] = org.notification_url

            user_profile['organizations'].append(org_info)

        if 'street' in profile.tax_address:
            user_profile['tax_address'] = {
                'street': profile.tax_address['street'],
                'postal': profile.tax_address['postal'],
                'city': profile.tax_address['city'],
                'country': profile.tax_address['country']
            }

        # Include roles for the user
        user_profile['roles'] = profile.get_user_roles()

        if user.is_staff:
            user_profile['roles'].append('admin')

        if 'number' in profile.payment_info:
            user_profile['payment_info'] = {}
            number = profile.payment_info['number']
            number = 'xxxxxxxxxxxx' + number[-4:]
            user_profile['payment_info']['number'] = number
            user_profile['payment_info']['type'] = profile.payment_info['type']
            user_profile['payment_info']['expire_year'] = profile.payment_info['expire_year']
            user_profile['payment_info']['expire_month'] = profile.payment_info['expire_month']
            user_profile['payment_info']['cvv2'] = profile.payment_info['cvv2']

        if profile.provider_requested:
            user_profile['provider_request'] = True

        return HttpResponse(json.dumps(user_profile), status=200, mimetype='application/json')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, username):

        if not request.user.is_staff and not request.user.username == username:
            return build_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)
        # Update the user
        try:
            user = User.objects.get(username=username)
            # Get the user profile
            user_profile = UserProfile.objects.get(user=user)

            # If WStore is not integrated with the accounts enabler
            # update user info and roles
            if not settings.OILAUTH:
                if 'admin' in data['roles'] and request.user.is_staff:
                    user.is_staff = True

                if 'password' in data:
                    user.set_password(data['password'])

                if 'provider' in data['roles']:
                    # Append the provider role to the user
                    orgs = []
                    for o in user_profile.organizations:
                        if Organization.objects.get(pk=o['organization']).name == user.username:
                            if not 'provider' in o['roles']:
                                o['roles'].append('provider')

                        orgs.append(o)

                    user_profile.organizations = orgs

                elif not 'provider' in data['roles'] and 'provider' in user_profile.get_user_roles():
                    # Remove the provider role from the user info
                    orgs = []
                    for o in user_profile.organizations:

                        if Organization.objects.get(pk=o['organization']).name == user.username:
                            o['roles'].remove('provider')
                            orgs.append(o)
                        else:
                            orgs.append(o)

                    user_profile.organizations = orgs

                if 'notification_url' in data and 'provider' in user_profile.get_user_roles():
                    user_org = Organization.objects.get(name=user.username)
                    user_org.notification_url = data['notification_url']
                    user_org.save()

                if 'first_name' in data and 'last_name' in data:
                    user.first_name = data['first_name']
                    user.last_name = data['last_name']
                    user_profile.complete_name = data['first_name'] + ' ' + data['last_name']
            else:
                if 'notification_url' in data and 'provider' in user_profile.get_current_roles():
                    user_org = user_profile.current_organization;
                    if user.pk in user_org.managers:
                        user_org.notification_url = data['notification_url']
                        user_org.save()
                    else:
                        return build_response(request, 401, 'You do not have permission to modify the notification URL of you current organization')

            if 'tax_address' in data:
                user_profile.tax_address = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'country': data['tax_address']['country']
                }
            else:
                # the update is absolute so if no tax address provided it is deleted
                user_profile.tax_address = {}

            if 'payment_info' in data:

                number = data['payment_info']['number']

                if not is_valid_credit_card(number):
                    if 'number' in user_profile.payment_info and \
                    is_hidden_credit_card(number, user_profile.payment_info['number']):
                        number = user_profile.payment_info['number']
                    else:
                        raise Exception('')

                user_profile.payment_info = {
                    'type': data['payment_info']['type'],
                    'number': number,
                    'expire_month': data['payment_info']['expire_month'],
                    'expire_year': data['payment_info']['expire_year'],
                    'cvv2': data['payment_info']['cvv2']
                }
            else:
                # the update is absolute so if no payment info provided it is deleted
                user_profile.payment_info = {}

            user.save()
            user_profile.save()

        except:
            return build_response(request, 400, 'Invalid content')

        return build_response(request, 200, 'OK')

    @authentication_required
    def delete(self, request, username):
        pass


def reset_user(request, username):

    user = User.objects.get(username=username)
    user.userprofile.offerings_purchased = []
    user.userprofile.save()

    purchases = Purchase.objects.filter(customer=user)
    for p in purchases:
        try:
            p.contract.delete()
        except:
            pass
        p.delete()

    return build_response(request, 200, 'OK')


class OrganizationCollection(Resource):

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        try:
            data = json.loads(request.raw_post_data)

            tax_address = {}
            if 'tax_address' in data:
                tax_address = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'country': data['tax_address']['country']
                }

            payment_info = {}
            if 'payment_info' in data:
                if not is_valid_credit_card(data['payment_info']['number']):
                    raise Exception()

                payment_info = {
                    'type': data['payment_info']['type'],
                    'number': data['payment_info']['number'],
                    'expire_month': data['payment_info']['expire_month'],
                    'expire_year': data['payment_info']['expire_year'],
                    'cvv2': data['payment_info']['cvv2']
                }
            Organization.objects.create(
                name=data['name'],
                notification_url=data['notification_url'],
                tax_address=tax_address,
                payment_info=payment_info,
		private=False
            )
        except:
            return build_response(request, 400, 'Inavlid content')

        return build_response(request, 201, 'Created')

    @authentication_required
    def read(self, request):

        response = []

        for org in Organization.objects.all():
            if not org.private:
                org_element = {
                    'name': org.name,
                    'notification_url': org.notification_url,
                    'tax_address': org.tax_address
                }
                if 'number' in org.payment_info:
                    number = org.payment_info['number']
                    number = 'xxxxxxxxxxxx' + number[-4:]
                    org_element['payment_info'] = {
                        'number': number,
                        'type': org.payment_info['type'],
                        'expire_year': org.payment_info['expire_year'],
                        'expire_month': org.payment_info['expire_month'],
                        'cvv2': org.payment_info['cvv2'],
                    }

                response.append(org_element)

        return HttpResponse(json.dumps(response), status=200, mimetype='appliacation/json')


class OrganizationEntry(Resource):

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, org):

        # Get the organization
        try:
            organization = Organization.objects.get(name=org)
        except:
            return build_response(request, 404, 'Not found')

        if not request.user.is_staff or not request.user.pk in organization.managers:
            return build_response(request, 403, 'Forbidden')

        try:
            # Load request data
            data = json.loads(request.raw_post_data)
            organization.notification_url = data['notification_url']

            # Load the tax address
            new_taxaddr = {}
            if 'tax_address' in data and data['tax_address'] != {}:
                new_taxaddr = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'country': data['tax_address']['country']
                }

            organization.tax_address = new_taxaddr

            # Load the payment info
            new_payment = {}
            if 'payment_info' in data and data['payment_info'] != {}:

                number = data['payment_info']['number']

                if not is_valid_credit_card(number):
                    if 'number' in organization.payment_info and \
                    is_hidden_credit_card(number, organization.payment_info['number']):
                        number = organization.payment_info['number']
                    else:
                        raise Exception('')

                new_payment = {
                    'type': data['payment_info']['type'],
                    'number': number,
                    'expire_year': data['payment_info']['expire_year'],
                    'expire_month': data['payment_info']['expire_month'],
                    'cvv2': data['payment_info']['cvv2']
                }

            organization.payment_info = new_payment
            organization.save()
        except:
            return build_response(request, 400, 'Invalid Content')

        return build_response(request, 200, 'OK')


class UnitCollection(Resource):

    @authentication_required
    def read(self, request):

        response = []
        for unit in Unit.objects.all():
            u = {
                'name': unit.name,
                'defined_model': unit.defined_model
            }

            if unit.defined_model == 'subscription':
                u['renovation_period'] = unit.renovation_period

            response.append(u)

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json;charset=UTF-8')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        # The that the user is an admin
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        try:
            unit_data = json.loads(request.raw_post_data)
        except:
            return build_response(request, 400, 'Invalid JSON content')

        # Check the content of the request
        if not 'name' in unit_data or not 'defined_model' in unit_data:
            return build_response(request, 400, 'Missing required field')

        # Check that the new unit does not exist
        u = Unit.objects.filter(name=unit_data['name'])
        if len(u) > 0:
            return build_response(request, 400, 'The unit already exists')

        # Check the pricing model defined
        if unit_data['defined_model'].lower() != 'single payment' and \
        unit_data['defined_model'].lower() != 'subscription' and \
        unit_data['defined_model'].lower() != 'pay per use':
            return build_response(request, 400, 'Invalid pricing model')

        # Check the renovation period
        if unit_data['defined_model'].lower() == 'subscription' and \
        not 'renovation_period' in unit_data:
            return build_response(request, 400, 'Missing renovation period')

        # Create the unit
        if 'renovation_period' in unit_data:
            Unit.objects.create(
                name=unit_data['name'],
                defined_model=unit_data['defined_model'].lower(),
                renovation_period=unit_data['renovation_period'])
        else:
            Unit.objects.create(
                name=unit_data['name'],
                defined_model=unit_data['defined_model'].lower())

        return build_response(request, 201, 'Created')


@login_required
@require_http_methods(['PUT'])
def change_current_organization(request):

    # Get the requested organization
    data = json.loads(request.raw_post_data)
    try:
        org = Organization.objects.get(name=data['organization'])
    except:
        return build_response(request, 404, 'Not found')

    # Check that the user belongs to the organization
    found = False
    for o in request.user.userprofile.organizations:
        if o['organization'] == org.pk:
            found = True
            break

    if not found:
        return build_response(request, 403, 'Forbidden')

    # Change the current organization
    request.user.userprofile.current_organization = org
    request.user.userprofile.save()

    return build_response(request, 200, 'OK')


class OrganizationUserCollection(Resource):

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request, org):

        if settings.OILAUTH:
            return build_response(request, 403, 'It is not possible to modify organizations (use Account enabler instead)')

        try:
            organization = Organization.objects.get(name=org)
        except:
            return build_response(request, 404, 'Organization not found')

        # Check if the organization is private
        if organization.private:
            return build_response(request, 403, 'Forbidden')
    
        # Check if the user can include users in the organization
        if not request.user.is_staff and not request.user.pk in organization.managers:
            return build_response(request, 403, 'Forbidden')

        # Get the user
        try:
            data = json.loads(request.raw_post_data)
            user = User.objects.get(username=data['user'])

            if not 'roles' in data:
                raise Exception('')
        except:
            return build_response(request, 400, 'Invalid JSON content')

        org_roles = []
        if 'provider' in data['roles']:
            org_roles.append('provider')

        if 'customer' in data['roles']:
            org_roles.append('customer')

        # Check if the user already belongs to the organization
        belongs = False
        for o in user.userprofile.organizations:
            if o['organization'] == organization.pk:
                belongs = True

        if belongs == True:
            return build_response(request, 400, 'The user already belongs to the organization')

        # Include the new user
        user.userprofile.organizations.append({
            'organization': organization.pk,
            'roles': org_roles
        })
        user.userprofile.save()

        return build_response(request, 200, 'OK')