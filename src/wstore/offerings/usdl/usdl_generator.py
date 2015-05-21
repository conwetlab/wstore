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
from rdflib import Namespace, BNode, Literal
from rdflib.namespace import RDF, DCTERMS, RDFS
from urlparse import urljoin

from django.template import loader
from django.template import Context as TmplContext

from wstore.models import Context, Resource
from wstore.charging_engine.models import Unit


PRICE = Namespace("http://www.linked-usdl.org/ns/usdl-pricing#")
USDL = Namespace("http://www.linked-usdl.org/ns/usdl-core#")
GR = Namespace("http://purl.org/goodrelations/v1#")
SPIN = Namespace('http://spinrdf.org/spin#')
SP = Namespace('http://spinrdf.org/sp#')


class USDLGenerator():

    _allowed_formats = ('application/rdf+xml', 'n3', 'json-ld')

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
            if 'label' not in component:
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

                self._validate_currency(plan['currency'])

    def _generate_bind_expression(self, graph, expression_node, bind_info):
        types_ = {
            '+': 'Sum',
            '*': 'Mul',
            '-': 'Minus',
            '/': 'Div'
        }

        graph.add((expression_node, RDF.type, SP[types_[bind_info['operation']]]))

        arg1 = BNode()
        arg1_val = BNode()
        if isinstance(bind_info['arg1'], dict):
            self._generate_bind_expression(graph, arg1_val, bind_info['arg1'])
        else:
            graph.add((arg1_val, SP['varName'], bind_info['arg1']))

        graph.add((arg1, SP['arg1'], arg1_val))

        arg2 = BNode()
        arg2_val = BNode()
        if isinstance(bind_info['arg2'], dict):
            self._generate_bind_expression(graph, arg2_val, bind_info['arg2'])
        else:
            graph.add((arg2_val, SP['varName'], bind_info['arg2']))

        graph.add((arg2, SP['arg2'], arg2_val))

    def _generate_price_funtion(self, graph, component_node, component_info):
        # Include text description of the function
        graph.add((component_node, PRICE['hasTextFunction'], Literal(component_info['text_function'])))

        # Build the price function
        function_node = BNode()
        graph.add((function_node, RDF.type, SPIN['Function']))
        graph.add((function_node, RDFS.label, Literal(component_info['price_function']['label'])))

        body_node = BNode()
        graph.add((body_node, RDF.type, SP['Select']))

        var_nodes = {}

        # Create variables definition
        for var_id, value in component_info['price_function']['variables'].iteritems():
            # Build variable
            variable_node = BNode()

            type_ = 'Usage'
            if value['type'] == 'constant':

                type_ = 'Constant'
                value_node = BNode()
                graph.add((value_node, RDF.type, GR['QuantitativeValue']))
                graph.add((value_node, GR['hasValueFloat'], Literal(value['value'])))
                graph.add((variable_node, PRICE['hasValue'], value_node))

            graph.add((variable_node, RDF.type, PRICE[type_]))
            graph.add((variable_node, RDFS.label, Literal(value['label'])))

            graph.add((function_node, PRICE['hasVariable'], variable_node))

            var_nodes[var_id] = variable_node

        # Build result list
        res_list = BNode()
        graph.add((res_list, RDF.type, RDF.List))

        res_first = BNode()
        graph.add((res_first, SP['varName'], Literal['price']))
        graph.add((res_list, RDF.first, res_first))
        graph.add((res_list, RDF.rest, RDF.nil))

        graph.add((body_node, SP['resultVariables'], res_list))

        # Build where clause
        where_list = BNode()
        graph.add((where_list, RDF.type, RDF.List))
        graph.add((body_node, SP['where'], where_list))

        for var_id, var_node in var_nodes.iteritems():
            # Generate first element for the variable (bind value object)
            where_first = BNode()

            graph.add((where_first, SP['subject'], var_node))
            graph.add((where_first, SP['predicate'], PRICE['hasValue']))

            ob_node = BNode()
            graph.add((ob_node, SP['varName'], Literal(var_id + '_value')))
            graph.add((where_first, SP['object'], ob_node))

            graph.add((where_list, RDF.first, where_first))

            where_rest = BNode()
            graph.add((where_rest, RDF.type, RDF.List))
            graph.add((where_list, RDF.rest, where_rest))

            where_list = where_rest

            # Generate second element for the variable (bind float value)
            where_first = BNode()

            sb_node = BNode()
            graph.add((ob_node, SP['varName'], Literal(var_id + '_value')))
            graph.add((where_first, SP['subject'], sb_node))

            graph.add((where_first, SP['predicate'], GR['hasValueFloat']))

            ob_node = BNode()
            graph.add((ob_node, SP['varName'], Literal(var_id)))
            graph.add((where_first, SP['object'], ob_node))

            graph.add((where_list, RDF.first, where_first))

            where_rest = BNode()
            graph.add((where_rest, RDF.type, RDF.List))
            graph.add((where_list, RDF.rest, where_rest))

            where_list = where_rest

        # Build bind expression
        bind_node = BNode()
        graph.add((bind_node, RDF.type, SP['bind']))

        expression_node = BNode()
        self._generate_bind_expression(graph, expression_node, component_info['price_function']['function'])

        graph.add((bind_node, SP['expression'], expression_node))

        # Include result variable for bind expression
        var_bind_node = BNode()
        graph.add((var_bind_node, SP['varName'], Literal('price')))
        graph.add((bind_node, SP['variable'], var_bind_node))

        # End where clause
        graph.add((where_list, RDF.first, bind_node))
        graph.add((where_list, RDF.rest, RDF.nil))

        graph.add((function_node, SPIN['body'], body_node))

        # Include the price function
        graph.add((component_node, PRICE['hasPriceFunction'], function_node))

    def _generate_price(self, graph, component_node, component_info, currency):
        price_node = BNode()

        graph.add((price_node, RDF.type, GR['PriceSpecification']))
        graph.add((price_node, GR['hasCurrency'], Literal(currency)))
        graph.add((price_node, GR['hasCurrencyValue'], Literal(component_info['value'])))
        graph.add((price_node, GR['hasUnitOfMeasurement'], Literal(component_info['unit'])))

        graph.add((component_node, PRICE['hasPrice'], price_node))

    def _generate_component(self, graph, plan_node, component_info, currency, is_deduction=False):
        comp = BNode()

        type_ = 'Deduction' if is_deduction else 'PriceComponent'

        # Include basic component info
        graph.add((comp, RDF.type, PRICE[type_]))
        graph.add((comp, RDFS.label, Literal(component_info['label'])))
        graph.add((comp, DCTERMS.description, Literal(component_info['description'])))

        # Check if the component is a basic component or a price funtion
        if 'text_function' in component_info:
            self._generate_price_funtion(graph, comp, component_info)
        else:
            self._generate_price(graph, comp, component_info, currency)

        # Include price component to the price plan
        graph.add((plan_node, PRICE['hasPriceComponent'], comp))

    def _generate_pricing(self, usdl, pricing_info, format_):
        # Create a graph with the existing basic usdl document

        graph = rdflib.ConjunctiveGraph()
        graph.parse(data=usdl, format='application/rdf+xml')

        offering_node = graph.subjects(RDF.type, USDL['ServiceOffering']).next()

        # Create price plans
        for plan in pricing_info['price_plans']:
            # Create a white node for the plan
            plan_node = BNode()

            # Include RDF type
            graph.add((plan_node, RDF.type, PRICE['PricePlan']))

            # Include title
            graph.add((plan_node, DCTERMS.title, Literal(plan['title'])))

            # Include description
            graph.add((plan_node, DCTERMS.description, Literal(plan['description'])))

            # Include price components if existing
            if 'price_components' in plan:
                for component in plan['price_components']:
                    self._generate_component(graph, plan_node, component, plan['currency'])

            # Include discounts if existing
            if 'deductions' in plan:
                for deduction in plan['deductions']:
                    self._generate_component(graph, plan_node, deduction, plan['currency'], is_deduction=True)

            # Bind the price plan
            graph.add((offering_node, USDL['hasPricePlan'], plan_node))

        # Seruialize the result in the specified format
        return graph.serialize(format=format_, auto_compact=True)

    def generate_offering_usdl(self, offering, format_='application/rdf+xml'):

        if format_ not in self._allowed_formats:
            raise ValueError('The specified format (' + format_ + ') is not a valid format')

        offering_info = offering.offering_description
        self.validate_info(offering_info, offering.open)

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
            usdl = self._generate_pricing(usdl, offering_info['pricing'], format_)

        # Return the usdl in the spified format if not rendered yet
        elif format_ != 'application/rdf+xml':
            graph = rdflib.Graph()
            graph.parse(data=usdl, format='application/rdf+xml')
            usdl = graph.serialize(format=format_, auto_compact=True)

        # Return the USDL document
        return usdl
