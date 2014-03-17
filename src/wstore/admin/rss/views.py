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
from urllib2 import HTTPError

from django.http import HttpResponse
from django.conf import settings

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_response, supported_request_mime_types, \
authentication_required
from wstore.rss_adaptor.expenditure_manager import ExpenditureManager
from wstore.models import RSS, Context


class RSSCollection(Resource):

    @authentication_required
    def read(self, request):

        response = []

        for rss in RSS.objects.all():
            response.append({
                'name': rss.name,
                'host': rss.host
            })

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        # Only the admin can register new RSS instances
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)

        if not 'name' in data or not 'host':
            return build_response(request, 400, 'Invalid JSON content')

        # Check if the information provided is not already registered
        if len(RSS.objects.filter(name=data['name'])) > 0 or \
        len(RSS.objects.filter(host=data['host'])) > 0:
            return build_response(request, 400, 'Invalid JSON content')

        limits = {}
        cont = Context.objects.all()[0]

        # Check request limits
        if 'limits' in data:
            user_limits = data['limits']

            if not 'currency' in user_limits:
                # Load default currency
                user_limits['currency'] = cont.allowed_currencies['default']

            elif not cont.is_valid_currency(user_limits['currency']):
                # Check that the currency is valid
                return build_response(request, 400, 'Invalid currency')

            if 'transaction' in user_limits and (type(user_limits['transaction']) == float or \
            type(user_limits['transaction']) == int or (type(user_limits['transaction']) == unicode and \
            user_limits['transaction'].isdigit())):
                limits['perTransaction'] = float(user_limits['transaction'])

            if 'weekly' in user_limits and (type(user_limits['weekly']) == float or \
            type(user_limits['weekly']) == int or (type(user_limits['weekly']) == unicode and \
            user_limits['weekly'].isdigit())):
                limits['weekly'] = float(user_limits['weekly'])

            if 'daily' in user_limits and (type(user_limits['daily']) == float or \
            type(user_limits['daily']) == int or (type(user_limits['daily']) == unicode and \
            user_limits['daily'].isdigit())):
                limits['daily'] = float(user_limits['daily'])

            if 'monthly' in user_limits and (type(user_limits['monthly']) == float or \
            type(user_limits['monthly']) == int or (type(user_limits['monthly']) == unicode and \
            user_limits['monthly'].isdigit())):
                limits['monthly'] = float(user_limits['monthly'])

            if len(limits):
                limits['currency'] = user_limits['currency']

        if not len(limits):
            # Set default limits
            limits = {
                'currency': cont.allowed_currencies['default'],
                'perTransaction':10000,
                'weekly': 100000,
                'daily': 10000,
                'monthly': 100000
            }

        # Create the new entry
        rss = RSS.objects.create(
            name=data['name'],
            host=data['host'],
            expenditure_limits=limits)

        error = False
        code = None
        msg = None
        try:
            exp_manager = ExpenditureManager(rss, request.user.userprofile.access_token)
            # Create default expenditure limits
            exp_manager.set_provider_limit()

        except HTTPError as e:
            # Unauthorized: Maybe the token has expired
            if e.code == 401:
                try:
                    # Try to refresh the access token
                    social = request.user.social_auth.filter(provider='fiware')[0]
                    social.refresh_token()

                    # Update credentials
                    social = request.user.social_auth.filter(provider='fiware')[0]
                    credentials = social.extra_data

                    request.user.userprofile.access_token = credentials['access_token']
                    request.user.userprofile.refresh_token = credentials['refresh_token']
                    request.user.userprofile.save()

                    # Refresh expenditure manager user info
                    rss = RSS.objects.get(name=data['name'])
                    rss.access_token = credentials['access_token']
                    rss.save()
                    exp_manager = ExpenditureManager(rss, credentials['access_token'])
                    # Make the request again
                    exp_manager.set_provider_limit()
                except:
                    error = True
                    code = 401
                    msg = "You don't have access to the RSS instance requested"

            # Server error
            else:
                error = True
                code = 502
                msg = 'The RSS has failed creating the expenditure limits'

        # Not an HTTP error
        except Exception as e:
            error = True
            code = 400
            msg = e.message


        if error:
            # Remove created RSS entry
            rss.delete()
            # Return error response
            return build_response(request, code, msg)

        # The request has been success so the used credentials are valid
        if settings.OILAUTH:
            # Store the credentials for future access
            rss.access_token = request.user.userprofile.access_token
            rss.refresh_token = request.user.userprofile.request_token
            rss.save()


        return build_response(request, 201, 'Created')


class RSSEntry(Resource):

    @authentication_required
    def read(self, request, rss):

        try:
            rss_model = RSS.objects.get(name=rss)
            response = {
                'name': rss_model.name,
                'host': rss_model.host
            }
        except:
            return build_response(request, 400, 'Invalid request')

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @authentication_required
    def delete(self, request, rss):

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        try:
            rss_model = RSS.objects.get(name=rss)
            rss_model.delete()
        except:
            return build_response(request, 400, 'Invalid request')

        return build_response(request, 204, 'No content')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, rss):
        pass

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request, rss):
        pass