# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

import rdflib
from urlparse import urljoin

from django.template import loader
from django.template import Context as TmplContext

from wstore.models import Context, Resource
from wstore.charging_engine.models import Unit


class USDLGenerator():

    _allowed_formats = ('xml', 'n3', 'json-ld')

    def validate_info(self, offering_info, open_=False):
        # Validate USDL mandatory fields
        if 'description' not in offering_info or 'base_id' not in offering_info \
                or 'organization' not in offering_info or 'name' not in offering_info \
                or 'version' not in offering_info or 'image_url' not in offering_info \
                or 'created' not in offering_info or 'abstract' not in offering_info \
                or 'pricing' not in offering_info or 'modified' not in offering_info:

            raise ValueError('Invalid offering info: Missing a required field')

        # Validate that description field is not empty
        if not offering_info['description']:
            raise ValueError('Invalid offering info: Description field cannot be empty')

        # Validate legal fields
        if 'legal' in offering_info:
            if 'title' not in offering_info['legal'] or 'text' not in offering_info['legal']:
                raise ValueError('Invalid offering info: Title and text fields are required if providing legal info')

            if not offering_info['legal']['title'] or not offering_info['legal']['text']:
                raise ValueError('Invalid offering info: Title and text fields cannot be empty in legal info')

        self._validate_pricing(offering_info['pricing'], open_=open_)

    def _validate_currency(self, currency):
        context = Context.objects.all()[0]

        if 'allowed' not in context.allowed_currencies:
            raise ValueError("There are'n currencies registered in WStore, please contact with an admin")

        found = False
        i = 0
        while not found and i < len(context.allowed_currencies['allowed']):
            if currency.lower() == context.allowed_currencies['allowed'][i]['currency'].lower():
                found = True
            i += 1

        if not found:
            raise ValueError('Invalid pricing info: The currency ' + currency + ' is not supported')

    def _validate_arguments(self, function, variables):
        allowed_op = ('+', '*', '-', '/')

        if 'operation' not in function:
            raise ValueError('Invalid pricing info: Missing required field operation in price function')

        if function['operation'] not in allowed_op:
            raise ValueError('Invalid pricing info: Operation ' + function['operation'] + ' is not supported')

        if 'arg1' not in function:
            raise ValueError('Invalid pricing info: Missing required field arg1 in price function')

        if isinstance(function['arg1'], dict):
            self._validate_arguments(function['arg1'], variables)
        elif function['arg1'] not in variables:
            raise ValueError('Invalid pricing info: Variable ' + function['arg1'] + ' not declared')

        if 'arg2' not in function:
            ValueError('Invalid pricing info: Missing required field arg1 in price function')

        if isinstance(function['arg2'], dict):
            self._validate_arguments(function['arg2'], variables)
        elif function['arg2'] not in variables:
            raise ValueError('Invalid pricing info: Variable ' + function['arg2'] + ' not declared')

    def _validate_price_function(self, function):
        if 'label' not in function:
            raise ValueError('Invalid pricing info: Missing required field "label" in price function')

        if 'variables' not in function:
            raise ValueError('Invalid pricing info: Missing required field "variables" in price function')

        for k, var in function['variables'].iteritems():
            if 'label' not in var:
                raise ValueError('Invalid pricing info: Missing required field "label" in price function variable')

            if 'type' not in var:
                raise ValueError('Invalid pricing info: Missing required field "type" in price function variable')

            if var['type'].lower() != 'usage' and var['type'].lower() != 'constant':
                raise ValueError('Invalid pricing info: Invalid variable type ' + var['type'] + ' in price funtion variable, allowed are: usage, constant')

            if var['type'].lower() == 'constant' and 'value' not in var:
                raise ValueError('Invalid pricing info: Missing required field "value" in price function constant')

            if 'value' in var:
                try:
                    float(var['value'])
                except:
                    raise TypeError('Invalid pricing info: value field in price function variables must be a number, found: ' + unicode(var['value']))

        if 'function' not in function:
            raise ValueError('Invalid pricing info: Missing required field function in price function')

        self._validate_arguments(function['function'], function['variables'])

    def _validate_components(self, components, is_deduction=False):
        for component in components:
            if 'title' not in component:
                raise ValueError('Invalid pricing info: Missing title field in price component')

            if 'description' not in component:
                raise ValueError('Invalid pricing info: Missing description field in price component')

            # Check if is a basic component or a price function
            if 'value' in component and 'unit' in component:
                # Validate unit
                units = Unit.objects.filter(name=component['unit'].lower())
                if not len(units):
                    raise ValueError('Invalid pricing info: A price component contains an unsupported unit: ' + component['unit'])

                if is_deduction and units[0].defined_model.lower() != 'pay per use':
                    raise ValueError('Invalid pricing info: Deductions only can define pay per use components')

                try:
                    float(component['value'])
                except:
                    raise TypeError('Invalid pricing info: The value of price components must be a number, found: ' + unicode(component['value']))

            elif 'text_function' in component and 'price_function' in component:
                self._validate_price_function(component['price_function'])
            else:
                raise ValueError('Invalid pricing info: A price component is not defining a pricing, value and unit fields are required for basic components and text_function and price_function fields are required for price functions')

            # Validate that only a pricing has been included
            if 'value' in component and 'unit' in component and \
                    'text_function' in component and 'price_function' in component:

                raise ValueError('Invalid pricing info: Only a pricing method (basic component or price function) is allowed in a price component')

    def _validate_pricing(self, pricing_info, open_=False):
        # Validate pricing fields
        if 'price_plans' not in pricing_info:
            raise ValueError('Invalid pricing info: Missing price_plans field')

        if not isinstance(pricing_info['price_plans'], list):
            raise TypeError('Invalid pricing info: price_plans field must be a list')

        if open_ and len(pricing_info['price_plans']) > 0:
            raise ValueError('Invalid pricing info: Open offerings cannot define price plans')

        # Validate price plans
        label_required = len(pricing_info['price_plans']) > 1
        labels = []

        for plan in pricing_info['price_plans']:

            if 'title' not in plan:
                raise ValueError('Invalid pricing info: Missing title field in price plan')

            if 'description' not in plan:
                raise ValueError('Invalid pricing info: Missing description field in price plan')

            if label_required and 'label' not in plan:
                raise ValueError('Invalid pricing info: label field is required in a price plan when more than one is provided')

            if 'label' in plan:
                if plan['label'] in labels:
                    raise ValueError('Invalid pricing info: label fields in price plans must be unique')

                labels.append(plan['label'])

            currency_required = False
            if 'price_components' in plan:
                currency_required = len(plan['price_components']) > 0
                self._validate_components(plan['price_components'])

            if 'deductions' in plan:
                currency_required = currency_required or len(plan['deductions']) > 0
                self._validate_components(plan['deductions'], is_deduction=True)

            # Validate currency
            if currency_required:

                if 'currency' not in plan:
                    raise ValueError('Invalid pricing info: Missing currency field')

                self._validate_currency(pricing_info['currency'])

    def generate_offering_usdl(self, offering, format_='xml'):

        if format_ not in self._allowed_formats:
            raise ValueError('The specified format (' + format_ + ') is not a valid format')

        offering_info = offering.offering_description
        self.validate_info(offering_info, offering_info['open'])

        # Get the template
        usdl_template = loader.get_template('usdl/basic_offering_usdl_template.rdf')

        site = Context.objects.all()[0].site.domain

        offering_uri = urljoin(site, 'api/offering/offerings/' + offering_info['organization'] + '/' + offering_info['name'] + '/' + offering_info['version'])
        image_url = urljoin(site, offering_info['image_url'])

        # Include resources
        resources = []
        for r in offering.resources:
            res = Resource.objects.get(pk=unicode(r))
            resources.append(res.resource_uri)

        context = {
            'offering_uri': offering_uri,
            'image_url': image_url,
            'name': offering_info['name'],
            'version': offering_info['version'],
            'description': offering_info['description'],
            'abstract': offering_info['abstract'],
            'created': offering_info['created'],
            'modified': offering_info['modified'],
            'base_id': offering_info['base_id'],
            'resources': resources
        }

        if 'legal' in offering_info:
            context['legal'] = True
            context['license_label'] = offering_info['legal']['title']
            context['license_description'] = offering_info['legal']['text']

        # Render the template
        usdl = usdl_template.render(TmplContext(context))

        # If a pricing model has been included generate it
        if len(offering_info['pricing']['price_plans']) > 0:
            usdl = self._generate_pricing(usdl, offering_info['pricing'])

        # Return the usdl in the spified format
        if format_ != 'xml':
            graph = rdflib.Graph()
            graph.parse(data=usdl, format='application/rdf+xml')
            usdl = graph.serialize(format=format_, auto_compact=True)

        # Return the USDL document
        return usdl

    def _generate_pricing(self, pricing_info):
        self._validate_pricing(pricing_info)
