# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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
from urllib2 import HTTPError

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings

from wstore.store_commons.utils.http import build_response, supported_request_mime_types, \
    authentication_required
from wstore.store_commons.utils.name import is_valid_id
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.resource import Resource
from wstore.models import UserProfile, RSS
from wstore.models import Organization
from wstore.admin.views import is_hidden_credit_card, is_valid_credit_card
from wstore.admin.rss.views import _check_limits
from wstore.rss_adaptor.rss_manager_factory import RSSManagerFactory


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
                user_profile['limits'] = user_org.expenditure_limits

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

                if user.pk in org.managers:
                    org_info['roles'].append('manager')

                if 'provider' in o['roles']:
                    org_info['notification_url'] = org.notification_url

                user_profile['organizations'].append(org_info)

            user_profile['tax_address'] = profile.tax_address

            # Include user roles
            user_profile['roles'] = profile.get_user_roles()

            if user.is_staff:
                user_profile['roles'].append('admin')

            user_profile['payment_info'] = {}
            if 'number' in profile.payment_info:
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

        # Check username format
        if not len(data['username']) > 4 or not is_valid_id(data['username']):
            return build_response(request, 400, 'Invalid username format')

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
                # Check notification URL format
                if data['notification_url'] and not is_valid_url(data['notification_url']):
                    raise Exception('Invalid notification URL format')

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
                    'province': data['tax_address']['province'],
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

        except Exception as e:
            return build_response(request, 400, unicode(e))

        return build_response(request, 201, 'Created')


class UserProfileEntry(Resource):

    @authentication_required
    def read(self, request, username):

        if not request.user.is_staff and not request.user.username == username:
            return build_response(request, 403, 'Forbidden')

        # Get user info
        user = User.objects.get(username=username)
        profile = user.userprofile

        user_profile = {}
        user_profile['username'] = user.username
        user_profile['complete_name'] = profile.complete_name

        if not settings.OILAUTH:
            user_profile['first_name'] = user.first_name
            user_profile['last_name'] = user.last_name
            user_org = Organization.objects.get(name=user.username)
        else:
            user_org = Organization.objects.get(actor_id=profile.actor_id)
            user_profile['limits'] = user_org.expenditure_limits

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

            if user.pk in org.managers and not profile.is_user_org():
                org_info['roles'].append('manager')

            if 'provider' in o['roles']:
                org_info['notification_url'] = org.notification_url

            user_profile['organizations'].append(org_info)

        if 'street' in profile.tax_address:
            user_profile['tax_address'] = profile.tax_address

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
                if request.user.is_staff and 'roles' in data:  # The user cannot change its roles
                    if 'admin' in data['roles'] and request.user.is_staff:
                        user.is_staff = True

                    if 'provider' in data['roles']:
                        # Append the provider role to the user
                        orgs = []
                        for o in user_profile.organizations:
                            if Organization.objects.get(pk=o['organization']).name == user.username \
                                    and 'provider' not in o['roles']:
                                o['roles'].append('provider')

                            orgs.append(o)

                        user_profile.organizations = orgs

                    elif 'provider' not in data['roles'] and 'provider' in user_profile.get_user_roles():
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

                if 'password' in data:
                    user.set_password(data['password'])

                if 'first_name' in data and 'last_name' in data:
                    user.first_name = data['first_name']
                    user.last_name = data['last_name']
                    user_profile.complete_name = data['first_name'] + ' ' + data['last_name']
                elif 'complete_name' in data:
                    user_profile.complete_name = data['complete_name']
            else:
                user_org = Organization.objects.get(actor_id=user.userprofile.actor_id)
                if 'notification_url' in data and 'provider' in user_profile.get_user_roles():
                    user_org.notification_url = data['notification_url']
                    user_org.save()

                # Check if expenditure limits are included in the request
                if 'limits' in data and data['limits']:
                    limits = _check_limits(data['limits'])
                    currency = limits['currency']
                    # Get default RSS instance
                    try:
                        rss_instance = RSS.objects.all()[0]
                    except:
                        raise Exception('No RSS instance registered: An RSS instance is needed for setting up expenditure limits')
                    # Create limits in the RSS
                    try:
                        rss_factory = RSSManagerFactory(rss_instance)
                        exp_manager = rss_factory.get_expenditure_manager(rss_instance.access_token)
                        exp_manager.set_actor_limit(limits, user.userprofile)
                    except HTTPError as e:
                        if e.code == 401:
                            rss_instance.refresh_token()
                            exp_manager.set_credentials(rss_instance.access_token)
                            exp_manager.set_actor_limit(limits, user.userprofile)
                        else:
                            raise e

                    # Save limits
                    limits['currency'] = currency
                    user_org.expenditure_limits = limits
                    user_org.save()

            if 'tax_address' in data:
                user_profile.tax_address = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'province': data['tax_address']['province'],
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

        except Exception as e:
            msg = 'Invalid content'
            if e.message:
                msg = e.message
            return build_response(request, 400, msg)

        return build_response(request, 200, 'OK')
