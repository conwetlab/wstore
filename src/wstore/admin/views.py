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

from wstore.store_commons.utils.http import build_response, supported_request_mime_types, \
authentication_required
from wstore.store_commons.resource import Resource
from wstore.models import UserProfile
from wstore.models import Organization


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
            user_profile = {}
            user_profile['username'] = user.username
            user_profile['first_name'] = user.first_name
            user_profile['last_name'] = user.last_name

            profile = UserProfile.objects.get(user=user)
            user_profile['organization'] = profile.organization.name
            user_profile['tax_address'] = profile.tax_address
            user_profile['roles'] = profile.roles

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

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)
        # Create the user
        try:
            user = User.objects.create(username=data['username'], first_name=data['first_name'], last_name=data['last_name'])

            if 'admin' in data['roles']:
                user.is_staff = True

            user.save()

            # Get the user profile
            user_profile = UserProfile.objects.get(user=user)
            org = Organization.objects.get(name=data['organization'])

            user_profile.organization = org

            if 'provider' in data['roles']:
                user_profile.roles.append('provider')

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

        user = User.objects.get(username=username)
        user_profile = {}
        user_profile['username'] = user.username
        user_profile['first_name'] = user.first_name
        user_profile['last_name'] = user.last_name

        profile = UserProfile.objects.get(user=user)
        user_profile['organization'] = profile.organization.name

        if 'street' in profile.tax_address:
            user_profile['tax_address'] = {
                'street': profile.tax_address['street'],
                'postal': profile.tax_address['postal'],
                'city': profile.tax_address['city'],
                'country': profile.tax_address['country']
            }

        user_profile['roles'] = profile.roles

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

        return HttpResponse(json.dumps(user_profile), status=200, mimetype='application/json')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, username):

        if not request.user.is_staff and not request.user.username == username:
            return build_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)
        # Create the user
        try:
            user = User.objects.get(username=username)

            if 'admin' in data['roles'] and request.user.is_staff:
                user.is_staff = True

            if 'password' in data:
                user.set_password(data['password'])

            user.first_name = data['first_name']
            user.last_name = data['last_name']

            # Get the user profile
            user_profile = UserProfile.objects.get(user=user)
            org = Organization.objects.get(name=data['organization'])

            user_profile.organization = org

            if 'provider' in data['roles'] and (not 'provider' in user_profile.roles):
                user_profile.roles.append('provider')

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
                payment_info=payment_info
            )
        except:
            return build_response(request, 400, 'Inavlid content')

        return build_response(request, 201, 'Created')

    @authentication_required
    def read(self, request):

        response = []

        for org in Organization.objects.all():
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