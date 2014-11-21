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
from urllib2 import HTTPError
from decimal import Decimal

from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.name import is_valid_id
from wstore.store_commons.utils.http import build_response, supported_request_mime_types, \
authentication_required, identity_manager_required
from wstore.rss_adaptor.expenditure_manager import ExpenditureManager
from wstore.rss_adaptor.model_manager import ModelManager
from wstore.rss_adaptor.utils.rss_errors import get_error_message
from wstore.models import RSS, RevenueModel, Context
from django.contrib.messages.api import get_messages


def _make_rss_request(manager, method, user):
    """
    Makes requests to the expenditure manager while
    manages the refresh of the access token
    """
    error = False
    code = None
    msg = None
    try:
        method()
    except HTTPError as e:
        # Unauthorized: Maybe the token has expired
        if e.code == 401:
            try:
                # Try to refresh the access token
                social = user.social_auth.filter(provider='fiware')[0]
                social.refresh_token()

                # Update credentials
                social = user.social_auth.filter(provider='fiware')[0]
                credentials = social.extra_data

                user.userprofile.access_token = credentials['access_token']
                user.userprofile.refresh_token = credentials['refresh_token']
                user.userprofile.save()

                # Refresh expenditure manager user info
                manager.set_credentials(credentials['access_token'])
                method()
            except:
                error = True
                code = 401
                msg = "You don't have access to the RSS instance requested"

        # Server error
        else:
            error = True
            code = 502
            msg = get_error_message(json.loads(e.read())['exceptionId'])

    # Not an HTTP error
    except Exception as e:
        error = True
        code = 400
        msg = unicode(e)

    return (error, code, msg)


def _check_limits(user_limits):
    """
    Check the provided limits included in a request
    """
    limits = {}
    limit_types = ('perTransaction', 'weekly', 'daily', 'monthly')

    cont = Context.objects.all()[0]

    if not 'currency' in user_limits:
        # Load default currency
        user_limits['currency'] = cont.allowed_currencies['default']

    elif not cont.is_valid_currency(user_limits['currency']):
        # Check that the currency is valid
        raise Exception('Invalid currency')

    # Get valid expenditure limits
    for t in limit_types:
        if t in user_limits and (type(user_limits[t]) == float or \
        type(user_limits[t]) == int or (type(user_limits[t]) == unicode and \
        user_limits[t].isdigit())):
            limits[t] = float(user_limits[t])

    if len(limits):
        limits['currency'] = user_limits['currency']

    return limits


def _check_revenue_models(models):
    """
    Check the revenue sharing models provided in the request
    """

    fixed_models = []
    found_models = []
    for model in models:
        # Check model contents
        if not 'class' in model or not 'percentage' in model:
            raise ValueError('Invalid revenue sharing model: Missing a required field')

        # Check product class
        if model['class'] != 'single-payment' and model['class'] != 'subscription' and model['class'] != 'use':
            raise ValueError('Invalid revenue sharing model: Invalid product class')
        else:
            found_models.append(model['class'])

        # Check percentage type
        try:
            model['percentage'] = float(model['percentage'])
        except:
            raise TypeError('Invalid revenue sharing model: Invalid percentage type')

        # Check percentage value
        if model['percentage'] < 0 or model['percentage'] > 100:
            raise ValueError('Invalid revenue sharing model: The percentage must be a number between 0 and 100')

        fixed_models.append(model)

    # Check that a percentage has been included for every needed product class
    if len(found_models) != 3 or not 'single-payment' in found_models\
     or not 'subscription' in found_models or not 'use' in found_models:
        raise ValueError('Invalid revenue sharing model: Missing a required product class')

    return fixed_models


class RSSCollection(Resource):

    @identity_manager_required
    @authentication_required
    def read(self, request):

        response = []

        for rss in RSS.objects.all():
            response.append({
                'name': rss.name,
                'host': rss.host,
                'limits': rss.expenditure_limits,
                'models': [{'revenue_class': model.revenue_class, 'percentage': unicode(model.percentage)} for model in rss.revenue_models]
            })

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @authentication_required
    @identity_manager_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        # Only the admin can register new RSS instances
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)

        if not 'name' in data or not 'host':
            return build_response(request, 400, 'RSS creation error: Missing a required field')

        # Check name regex
        if not is_valid_id(data['name']):
            return build_response(request, 400, 'RSS creation error: Invalid name format')

        # Check url regex
        if not is_valid_url(data['host']):
            return build_response(request, 400, 'RSS creation error: Invalid URL format')

        # Check if the information provided is not already registered
        if len(RSS.objects.filter(name=data['name'])) > 0 or \
        len(RSS.objects.filter(host=data['host'])) > 0:
            return build_response(request, 409, 'RSS creation error: The RSS instance already exists')

        limits = {}
        cont = Context.objects.all()[0]

        # Check request limits
        if 'limits' in data:
            try:
                limits = _check_limits(data['limits'])
            except Exception as e:
                return build_response(request, 400, unicode(e))

        if not len(limits):
            # Set default limits
            limits = {
                'currency': cont.allowed_currencies['default'],
                'perTransaction': 10000,
                'weekly': 100000,
                'daily': 10000,
                'monthly': 100000
            }

        # Check revenue sharing models
        sharing_models = []
        if 'models' in data:
            try:
                sharing_models = _check_revenue_models(data['models'])
            except Exception as e:
                return build_response(request, 400, unicode(e))
        else:
            # Set default revenue models
            sharing_models = [{
                'class': 'single-payment',
                'percentage': 10.0
            },{
                'class': 'subscription',
                'percentage': 20.0
            },{
                'class': 'use',
                'percentage': 30.0
            }]

        # Build revenue models
        db_revenue_models = [] 
        for model in sharing_models:
            db_revenue_models.append(RevenueModel(
                revenue_class=model['class'],
                percentage=Decimal(model['percentage'])
            ))

        # Create the new entry
        rss = RSS.objects.create(
            name=data['name'],
            host=data['host'],
            expenditure_limits=limits,
            revenue_models=db_revenue_models
        )

        exp_manager = ExpenditureManager(rss, request.user.userprofile.access_token)
        # Create default expenditure limits
        call_result = _make_rss_request(exp_manager, exp_manager.set_provider_limit, request.user)

        if call_result[0]:
            rss.delete()
            # Return error response
            return build_response(request, call_result[1], call_result[2])

        # Create default revenue sharing models
        model_manager = ModelManager(rss, request.user.userprofile.access_token)

        model_created = False
        for model in sharing_models:
            def call_model_creation():
                model_manager.create_revenue_model(model)

            call_result = _make_rss_request(model_manager, call_model_creation, request.user)

            if call_result[0] and not model_created:
                rss.delete()
                return build_response(request, call_result[1], call_result[2])
            elif not call_result[0]:
                model_created = True

        # The request has been success so the used credentials are valid
        # Store the credentials for future access
        rss.access_token = request.user.userprofile.access_token
        rss.refresh_token = request.user.userprofile.refresh_token
        rss.save()

        return build_response(request, 201, 'Created')


class RSSEntry(Resource):

    @identity_manager_required
    @authentication_required
    def read(self, request, rss):

        try:
            rss_model = RSS.objects.get(name=rss)
            response = {
                'name': rss_model.name,
                'host': rss_model.host,
                'limits': rss_model.expenditure_limits,
                'models': [{'revenue_class': model.revenue_class, 'percentage': unicode(model.percentage)} for model in rss.revenue_models]
            }
        except:
            return build_response(request, 400, 'Invalid request')

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @identity_manager_required
    @authentication_required
    def delete(self, request, rss):

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        # Get rss entry
        try:
            rss_model = RSS.objects.get(name=rss)
        except:
            return build_response(request, 404, 'Not found')

        # Delete provider limits
        exp_manager = ExpenditureManager(rss_model, request.user.userprofile.access_token)
        call_result = _make_rss_request(exp_manager, exp_manager.delete_provider_limit, request.user)

        if call_result[0]:
            return build_response(request, call_result[1], call_result[2])

        # Delete rs models
        model_manager = ModelManager(rss_model, request.user.userprofile.access_token)
        call_result = _make_rss_request(model_manager, model_manager.delete_provider_models, request.user)

        if call_result[0]:
            return build_response(request, call_result[1], call_result[2])

        # Delete rss model
        rss_model.delete()
        return build_response(request, 204, 'No content')

    @authentication_required
    @identity_manager_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, rss):
        """
        Makes a partial update, only name, limits and default selection
        """
        # Check if the user is staff
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        # Check rss
        try:
            rss_model = RSS.objects.get(name=rss)
        except:
            return build_response(request, 404, 'Not found')

        # Get data
        try:
            data = json.loads(request.raw_post_data)
        except:
            return build_response(request, 400, 'Invalid JSON data')

        # Check the name
        if 'name' in data and data['name'].lower() != rss.lower():
            # Check that the name does not exist
            exist = True
            try:
                RSS.objects.get(name=data['name'])
            except:
                exist = False

            if exist:
                return build_response(request, 400, 'The selected name is in use')

            rss_model.name = data['name']
            rss_model.save()

        limits = {}
        # Check if limits has been provided
        if 'limits' in data:
            limits = _check_limits(data['limits'])

        sharing_models = []
        if 'models' in data:
            try:
                sharing_models = _check_revenue_models(data['models'])
            except Exception as e:
                return build_response(request, 400, unicode(e))

        # Update expenditure limits
        if limits:
            old_limits = rss_model.expenditure_limits
            rss_model.expenditure_limits = limits
            rss_model.save()
            # Make the update request
            exp_manager = ExpenditureManager(rss_model, request.user.userprofile.access_token)
            call_result = _make_rss_request(exp_manager, exp_manager.set_provider_limit, request.user)

            if call_result[0]:
                # Reset expenditure limits
                rss_model.expenditure_limits = old_limits
                return build_response(request, call_result[1], call_result[2])

        # Update revenue sharing models
        if len(sharing_models):
            rss_model.revenue_models = []
            model_manager = ModelManager(rss_model, request.user.userprofile.access_token)

            # Update the models
            for model in sharing_models:
                revenue_model = RevenueModel(
                    revenue_class=model['class'],
                    percentage=Decimal(model['percentage'])
                )

                def call_model_creation():
                    model_manager.update_revenue_model(model)

                call_result = _make_rss_request(model_manager, call_model_creation, request.user)

                if call_result[0]:
                    return build_response(request, call_result[1], call_result[2])
                else:
                    rss_model.revenue_models.append(revenue_model)

        # Update credentials
        rss_model.access_token = request.user.userprofile.access_token
        rss_model.refresh_token = request.user.userprofile.refresh_token

        # Save the model
        rss_model.save()

        return build_response(request, 200, 'OK')
