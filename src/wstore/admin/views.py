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

from django.http import HttpResponse

from wstore.store_commons.utils.http import build_response, supported_request_mime_types, \
authentication_required
from wstore.store_commons.resource import Resource
from wstore.models import Context
from wstore.charging_engine.models import Unit


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


class CurrencyCollection(Resource):

    @authentication_required
    def read(self, request):

        # Check if the user is an admin
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        # Get Store context
        context = Context.objects.all()[0]
        # Return currencies
        if 'allowed' in context.allowed_currencies:
            currs = [{
                'currency': curr['currency'],
                'default': curr['currency'].lower() == context.allowed_currencies['default'].lower()
            } for curr in context.allowed_currencies['allowed']]
        else:
            currs = []

        response = json.dumps({
            'allowed_currencies': currs
        })
        return HttpResponse(response, status=200, mimetype='application/json; charset=utf-8')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):
        # Check if the user is an admin
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        # Get data
        data = json.loads(request.raw_post_data)
        if not 'currency' in data:
            return build_response(request, 400, 'Invalid JSON content')

        # Get the context
        context = Context.objects.all()[0]

        # Check if the allowed_currencies list is empty
        first = False
        if not 'allowed' in context.allowed_currencies:
            first = True
            context.allowed_currencies['allowed'] = []

        error = False
        # Check that the new currency is not already included
        for curr in context.allowed_currencies['allowed']:
            if curr['currency'].lower() == data['currency'].lower():
                error = True
                break

        if error:
            return build_response(request, 400, 'The currency already exists')

        # Check if it is the default currency
        if ('default' in data and data['default']) or first:
            # Note the this will override previous default currency
            context.allowed_currencies['default'] = data['currency']

        # Include new currency
        context.allowed_currencies['allowed'].append({
            'currency': data['currency'],
            'in_use': False
        })
        context.save()
        return build_response(request, 201, 'Created')


class CurrencyEntry(Resource):

    @authentication_required
    def update(self, request, currency):
        """
        This method is used to change the default currency
       """
        if not request.user.is_staff:
            build_response(request, 403, 'Forbidden')

        # Get the context
        context = Context.objects.all()[0]

        # Check that the currency exist
        if not 'default' in context.allowed_currencies:
            return build_response(request, 404, 'Not found')

        if not currency.lower() == context.allowed_currencies['default'].lower():
            for c in context.allowed_currencies['allowed']:
                if c['currency'].lower() == currency.lower():
                    break
            else:
                return build_response(request, 404, 'Not found')

        # Make the currency the default currency
        context.allowed_currencies['default'] = currency
        context.save()

        # Return response
        return build_response(request, 200, 'OK')

    @authentication_required
    def delete(self, request, currency):

        # Check if the user is an admin
        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

        # Get the context
        context = Context.objects.all()[0]

        if not 'allowed' in context.allowed_currencies:
            return build_response(request, 404, 'Not found')

        del_curr = None
        # Search the currency
        for curr in context.allowed_currencies['allowed']:
            if curr['currency'].lower() == currency.lower():
                del_curr = curr
                break
        else:
            return build_response(request, 404, 'Not found')

        # Check if is possible to delete the currency
        if  context.allowed_currencies['default'].lower() == currency.lower():
            return build_response(request, 400, 'The currency cannot be deleted: It is the default currency')

        if del_curr['in_use']:
            return build_response(request, 400, 'The currency cannot be deleted: An offering is using it')

        # Remove the currency
        context.allowed_currencies['allowed'].remove(del_curr)
        context.save()

        return build_response(request, 204, 'No content')
