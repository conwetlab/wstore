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

import rdflib

from django.utils.translation import ugettext as _

from wstore.models import Offering


FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
MSM = rdflib.Namespace('http://cms-wg.sti2.org/ns/minimal-service-model#')
OWL = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/')
USDL = rdflib.Namespace('http://www.linked-usdl.org/ns/usdl-core#')
LEGAL = rdflib.Namespace('http://www.linked-usdl.org/ns/usdl-legal#')
PRICE = rdflib.Namespace('http://www.linked-usdl.org/ns/usdl-pricing#')
SLA = rdflib.Namespace('http://www.linked-usdl.org/ns/usdl-sla#')
BLUEPRINT = rdflib.Namespace('http://bizweb.sap.com/TR/blueprint#')
VCARD = rdflib.Namespace('http://www.w3.org/2006/vcard/ns#')
XSD = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
CTAG = rdflib.Namespace('http://commontag.org/ns#')
ORG = rdflib.Namespace('http://www.w3.org/ns/org#')
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
TIME = rdflib.Namespace('http://www.w3.org/2006/time#')
GR = rdflib.Namespace('http://purl.org/goodrelations/v1#')
DOAP = rdflib.Namespace('http://usefulinc.com/ns/doap#')
GEO = rdflib.Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
SPIN = rdflib.Namespace('http://spinrdf.org/spin#')
SP = rdflib.Namespace('http://spinrdf.org/sp#')


class USDLParser(object):

    _usdl_document = None
    _graph = None
    _offering_uri = None

    def __init__(self, usdl_document, mime_type):
        self._usdl_document = usdl_document
        self._graph = rdflib.Graph()

        #Check rdf format
        if mime_type == 'application/rdf+xml':
            self._graph.parse(data=usdl_document, format="application/rdf+xml")
        elif mime_type == 'text/n3' or mime_type == 'text/turtle' or mime_type == 'text/plain':
            self._graph.parse(data=usdl_document, format='n3')
        elif mime_type == 'application/json':
            # For json-ld a conjuntive graph is needed
            self._graph = rdflib.ConjunctiveGraph()
            self._graph.parse(data=usdl_document, format='json-ld')
        else:
            msg = _('Error the document has not a valid rdf format')
            raise Exception(msg)

        offerings_number = 0
        # take all the services in the document
        for off in self._graph.subjects(RDF['type'], USDL['ServiceOffering']):
            self._offering_uri = off
            offerings_number = offerings_number + 1

        if offerings_number != 1:
            msg = _('No service offering has been defined')
            raise Exception(msg)

    def _get_field(self, namespace, element, predicate, id_=False):

        result = []

        for e in self._graph.objects(element, namespace[predicate]):
            if not id_:
                result.append(unicode(e))
            else:
                #If id = True means that the uri will be used so it is necesary to return the class
                result.append(e)

        if len(result) == 0:
            result.append('')

        return result

    def _parse_basic_info(self, service_uri):

        count = 0
        result = {}

        for t in self._graph.predicate_objects(service_uri):
            count = count + 1

        if count < 3:
            result['part_ref'] = True
            return

        result['part_ref'] = False
        vendor = self._get_field(USDL, service_uri, 'hasProvider', id_=True)[0]
        result['vendor'] = self._get_field(FOAF, vendor, 'name')[0]

        # provider vCard
        vcard = self._get_field(VCARD, vendor, 'adr', id_=True)[0]

        if vcard != '':
            result['vcard'] = {
                'BEGIN': [{
                    'properties': {},
                    'value':'VCARD',
                }],
                'FN': [{
                    'properties': {},
                    'value': result['vendor']
                }],
                'ADR': [{
                    'properties': {},
                    'value': self._get_field(VCARD, vcard, 'street-address')[0] + ';' + self._get_field(VCARD, vcard, 'postal-code')[0] + ';' + self._get_field(VCARD, vcard, 'locality')[0] + ';' + self._get_field(VCARD, vcard, 'country-name')[0]
                }],
                'TEL': [{
                    'properties': {},
                    'value': self._get_field(VCARD, vcard, 'tel')[0]
                }],
                'EMAIL': [{
                    'properties': {},
                    'value': self._get_field(VCARD, vcard, 'email')[0]
                }],
                'END': [{
                    'properties': {},
                    'value': "VCARD"
                }]
            }

        result['name'] = self._get_field(DCTERMS, service_uri, 'title')[0]

        version = self._get_field(USDL, service_uri, 'versionInfo')[0]
        service_parts = self._get_field(USDL, service_uri, 'hasPartMandatory', id_=True)

        if len(service_parts) > 0:
            result['parts'] = []
            for part in service_parts:
                part_info = {}
                part_info['name'] = self._get_field(DCTERMS, part, 'title')[0]
                part_info['uri'] = unicode(part)
                result['parts'].append(part_info)

        result['short_description'] = self._get_field(DCTERMS, service_uri, 'abstract')[0]
        result['long_description'] = self._get_field(DCTERMS, service_uri, 'description')[0]
        result['created'] = self._get_field(DCTERMS, service_uri, 'created')[0]
        result['modified'] = self._get_field(DCTERMS, service_uri, 'modified')[0]
        result['uriImage'] = self._get_field(FOAF, service_uri, 'depiction')[0]
        result['version'] = version
        result['page'] = self._get_field(FOAF, service_uri, 'page')[0]

        return result

    def _parse_legal_info(self, service_uri):

        result = []
        legal_conditions = self._get_field(USDL, service_uri, 'hasLegalCondition', id_=True)

        # If legal does not exist the method does nothing
        if len(legal_conditions) == 1 and legal_conditions[0] == '':
            return []

        for legal in legal_conditions:
            legal_condition = {
                'type': self._get_field(RDF, legal, 'type')[0],
                'label': self._get_field(DCTERMS, legal, 'title')[0],
                'description': self._get_field(DCTERMS, legal, 'description')[0],
                'clauses': [],
            }
            clauses = self._get_field(LEGAL, legal, 'hasClause', id_=True)

            for c in clauses:
                clause = {}
                clause['name'] = self._get_field(LEGAL, c, 'name')[0]
                clause['text'] = self._get_field(LEGAL, c, 'text')[0]
                legal_condition['clauses'].append(clause)

            result.append(legal_condition)

        return result

    def _parse_sla_info(self, service_uri):

        result = []
        service_level_profile = self._get_field(USDL, service_uri, 'hasServiceLevelProfile', id_=True)[0]

        #If sla does not exist the method does nothing
        if service_level_profile != '':
            service_levels = self._get_field(SLA, service_level_profile, 'hasServiceLevel', id_=True)

            for sla in service_levels:
                service_level = {
                    'type': self._get_field(RDF, sla, 'type')[0],
                    'name': self._get_field(DCTERMS, sla, 'title')[0],
                    'description': self._get_field(DCTERMS, sla, 'description')[0],
                    'obligatedParty': self._get_field(SLA, sla, 'obligatedParty')[0],
                    'slaExpresions': [],
                }

                sla_expresions = self._get_field(SLA, sla, 'serviceLevelExpression', id_=True)

                for exp in sla_expresions:
                    expresion = {
                        'name': self._get_field(DCTERMS, exp, 'title')[0],
                        'description': self._get_field(DCTERMS, exp, 'description')[0],
                        'variables': [],
                    }

                    variables = self._get_field(SLA, exp, 'hasVariable', id_=True)

                    for var in variables:
                        # The sla variables may defines service availibility or location, defined
                        # by a point in utm coodinates plus a radius, in this case this property is
                        # set in the sla expresion.
                        radius = False
                        default_value = self._get_field(SLA, var, 'hasDefault', id_=True)[0]

                        if default_value == '':
                            default_value = self._get_field(SLA, var, 'hasServiceRadius', id_=True)[0]
                            if default_value != '':
                                radius = True
                                if 'location' not in expresion:
                                    expresion['location'] = {}

                        type_ = self._get_field(RDF, default_value, 'type', id_=True)[0]

                        # The sla variable may contains a location, i.e service availability
                        if type_ == GR['QualitativeValue']:
                            location = self._get_field(GEO, default_value, 'location', id_=True)[0]
                            if location != '':
                                if 'location' not in expresion:
                                    expresion['location'] = {}

                                expresion['location']['coordinates'] = {
                                    'lat': self._get_field(GEO, location, 'lat')[0],
                                    'long': self._get_field(GEO, location, 'long')[0],
                                }
                        else:
                            variable_info = {
                                'label': self._get_field(RDFS, var, 'label')[0],
                                'type': self._get_field(RDF, default_value, 'type')[0],
                                'value': self._get_field(GR, default_value, 'hasValue')[0],
                                'unit': self._get_field(GR, default_value, 'hasUnitOfMeasurement')[0],
                            }

                            expresion['variables'].append(variable_info)
                            if radius:
                                expresion['location']['radius'] = variable_info

                    service_level['slaExpresions'].append(expresion)

                result.append(service_level)

        return result

    def _parse_interaction_protocols(self, service_uri):

        result = []
        # Get the interaction protocols that define the service functionality
        interaction_protocols = self._get_field(USDL, service_uri, 'hasInteractionProtocol', id_=True)

        if len(interaction_protocols) == 1 and interaction_protocols[0] == '':
            return []

        for itp in interaction_protocols:
            protocol_info = {
                'title': self._get_field(DCTERMS, itp, 'title')[0],
                'description': self._get_field(DCTERMS, itp, 'description')[0],
                'technical_interface': self._get_field(USDL, itp, 'hasTechnicalInterface')[0],
                'interactions': []
            }

            interactions = self._get_field(USDL, itp, 'hasInteraction', id_=True)

            for inte in interactions:
                interaction_info = {
                    'title': self._get_field(DCTERMS, inte, 'title')[0],
                    'description': self._get_field(DCTERMS, inte, 'description')[0],
                    'interface_operation': self._get_field(USDL, inte, 'hasInterfaceOperation')[0],
                    'inputs': [],
                    'outputs': []
                }

                for input_ in self._get_field(USDL, inte, 'hasInput', id_=True):
                    input_info = {
                        'label': self._get_field(RDFS, input_, 'label')[0],
                        'description': self._get_field(DCTERMS, input_, 'description')[0],
                        'interface_element': self._get_field(USDL, input_, 'hasInterfaceElement')[0]
                    }
                    interaction_info['inputs'].append(input_info)

                for output in self._get_field(USDL, inte, 'hasOutput', id_=True):
                    output_info = {
                        'label': self._get_field(RDFS, output, 'label')[0],
                        'description': self._get_field(DCTERMS, output, 'description')[0],
                        'interface_element': self._get_field(USDL, output, 'hasInterfaceElement')[0]
                    }
                    interaction_info['outputs'].append(output_info)

                protocol_info['interactions'].append(interaction_info)

            result.append(protocol_info)

        return result

    def _parse_bind_expression(self, expression):
        result = {}
        operations = {
            unicode(SP['Sum']): '+',
            unicode(SP['Minus']): '-',
            unicode(SP['Mul']): '*',
            unicode(SP['Div']): '/'
        }

        # Check the operation
        exp_type = self._get_field(RDF, expression, 'type', id_=True)
        if exp_type[0] == '':
            raise Exception('Invalid price function: An expression must contain an operation per level')

        try:
            op = operations[unicode(exp_type[0])]
        except:
            raise Exception('Invalid price function: Invalid operation')

        # Get arguments value
        arg1 = self._get_field(SP, expression, 'arg1', id_=True)[0]
        arg2 = self._get_field(SP, expression, 'arg2', id_=True)[0]

        if self._get_field(RDF, arg1, 'type', id_=True)[0] == '':
            # Get variable name
            result['arg1'] = self._get_field(SP, arg1, 'varName')[0]
        else:
            # arg1 is an expression
            result['arg1'] = self._parse_bind_expression(arg1)

        if self._get_field(RDF, arg2, 'type', id_=True)[0] == '':
            # Get variable name
            result['arg2'] = self._get_field(SP, arg2, 'varName')[0]
        else:
            # arg2 is an expression
            result['arg2'] = self._parse_bind_expression(arg2)

        result['operation'] = op
        return result

    def _parse_function(self, price_function):

        result = {
            'label': self._get_field(RDFS, price_function, 'label')[0],
            'variables': {},
            'function': {}
        }

        variables = []
        # Pre-process price variables
        for variable in self._get_field(PRICE, price_function, 'hasVariable', id_=True):
            # Check variable type to know if it is a constant or an usage
            # variable
            var_label = self._get_field(RDFS, variable, 'label')[0]
            var_type = self._get_field(RDF, variable, 'type', id_=True)[0]

            if var_type == PRICE['Constant']:
                val_part = self._get_field(PRICE, variable, 'hasValue', id_=True)[0]
                const_value = self._get_field(GR, val_part, 'hasValueFloat')

                # Check that the value is valid
                if len(const_value) == 1 and const_value[0] == '':
                    const_value = self._get_field(GR, val_part, 'hasValueInteger')

                    if len(const_value) != 1 or const_value[0] == '':
                        raise Exception('Invalid price function: Only a value is allowed for constants')

                variables.append({
                    'type': 'constant',
                    'id': variable,
                    'label': var_label,
                    'value': const_value[0]
                })
            elif var_type == PRICE['Usage']:
                variables.append({
                    'type': 'usage',
                    'id': variable,
                    'label': var_label
                })
            else:
                raise Exception('Invalid price function: Invalid variable type')

        # Get body expression
        function_body = self._get_field(SPIN, price_function, 'body', id_=True)[0]
        body_type = self._get_field(RDF, function_body, 'type', id_=True)[0]

        if body_type != SP['Select']:
            raise Exception('Invalid price function: Invalid SPARQL method')

        # Check where clause
        bind_expression = None
        matching_exp = {}

        # Iterate over expressions list
        exp_list = self._get_field(SP, function_body, 'where', id_=True)[0]

        # First element
        first = self._get_field(RDF, exp_list, 'first', id_=True)[0]
        # Rest of the list
        rest = self._get_field(RDF, exp_list, 'rest', id_=True)[0]
        nil = False

        while not nil:
            # Get expression node
            exp = first
            # Check bind expression
            exp_type = self._get_field(RDF, exp, 'type', id_=True)
            if len(exp_type) > 0 and exp_type[0] == SP['Bind']:
                if bind_expression == None:
                    bind_expression = exp
                else:
                    raise Exception('Invalid price function: Only a bind expression is allowed')
            else:
                # Get expression tuple
                subject = self._get_field(SP, exp, 'subject', id_=True)[0]
                predicate = self._get_field(SP, exp, 'predicate', id_=True)[0]
                object_ = self._get_field(SP, exp, 'object', id_=True)[0]

                # Check if the expression defines an aux name
                if predicate == PRICE['hasValue']:
                    variable_info = None
                    found = False
                    i = 0

                    while not found and i < len(variables):
                        if variables[i]['id'] == subject:
                            found = True
                            variable_info = variables[i]
                            variable_info['type'] = variables[i]['type']
                        i += 1

                    if not found:
                        raise Exception('Invalid price function: Variable not declared')

                    # Get the aux name
                    aux_name = self._get_field(SP, object_, 'varName')[0]

                    if aux_name in matching_exp:
                        # Check that is a variable name and not a
                        # duplicity in the expression
                        if 'variable_info' in matching_exp[aux_name]:
                            raise Exception('Invalid price function: Duplicated expression')

                        # The variable name used in the bind expression has
                        # already been processed
                        final_name = matching_exp[aux_name]['final_name']

                        # The variable and its name are bound so it is possible to store
                        # the variable info in the result structure
                        result['variables'][final_name] = {
                            'label': variable_info['label'],
                            'type': variable_info['type']
                        }

                        if variable_info['type'] == 'constant':
                            result['variables'][final_name]['value'] = variable_info['value']

                        # Store variable info in matching expression in order to avoid duplicity
                        matching_exp[aux_name]['variable_info'] = variable_info
                    else:
                        matching_exp[aux_name] = {
                            'variable_info': variable_info
                        }

                # Check if the expression defines a final name
                elif predicate == GR['hasValueFloat'] or predicate == GR['hasValueInteger']:
                    aux_name = self._get_field(SP, subject, 'varName')[0]
                    final_name = self._get_field(SP, object_, 'varName')[0]

                    if aux_name in matching_exp:
                        # Check that it contains variable info and
                        # not a duplicated final name
                        if 'final_name' in matching_exp[aux_name]:
                            raise Exception('Invalid price function: Duplicated expression')
                        # The variable has already been processed so it is possible
                        # to store the variable info in the result structure
                        result['variables'][final_name] = {
                            'label': matching_exp[aux_name]['variable_info']['label'],
                            'type': matching_exp[aux_name]['variable_info']['type']
                        }
                        if matching_exp[aux_name]['variable_info']['type'] == 'constant':
                            result['variables'][final_name]['value'] = matching_exp[aux_name]['variable_info']['value']

                        # Store the final name in matching expression to avoid duplicity
                        matching_exp[aux_name]['final_name'] = final_name
                    else:
                        matching_exp[aux_name] = {
                            'final_name': final_name
                        }
                else:
                    raise Exception('Invalid price function: Invalid predicate')

            # Check list pointer
            if rest == RDF['nil']:
                # There is not more elements
                nil = True
            else:
                # Update list pointer
                first = self._get_field(RDF, rest, 'first', id_=True)[0]
                rest = self._get_field(RDF, rest, 'rest', id_=True)[0]

        # Parse bind expression
        expression = self._get_field(SP, bind_expression, 'expression', id_=True)[0]

        # Parse the concrete function used to calculate the price
        result['function'] = self._parse_bind_expression(expression)

        # Build price function
        return result

    def _parse_pricing_info(self):

        result = {}

        # Parse offering info

        result['title'] = self._get_field(DCTERMS, self._offering_uri, 'title')[0]
        result['description'] = self._get_field(DCTERMS, self._offering_uri, 'description')[0]
        result['valid_from'] = self._get_field(USDL, self._offering_uri, 'validFrom')[0]
        result['valid_through'] = self._get_field(USDL, self._offering_uri, 'validThrough')[0]

        # Parse price plans info
        price_plans = self._get_field(USDL, self._offering_uri, 'hasPricePlan', id_=True)

        result['price_plans'] = []

        # Parse price plans
        for price in price_plans:
            price_plan = {}
            price_plan['title'] = self._get_field(DCTERMS, price, 'title')[0]
            price_plan['description'] = self._get_field(DCTERMS, price, 'description')[0]

            # Get the label of the price plan
            label = self._get_field(RDFS, price, 'label')

            if len(label) == 1:
                price_plan['label'] = label[0]
            elif len(label) > 1:
                raise Exception('Only a label is supported for the price plan')

            # Get price components
            price_components = self._get_field(PRICE, price, 'hasPriceComponent', id_=True)

            if len(price_components) > 1 or price_components[0] != '':
                # Initialize components and deductions
                price_plan['price_components'] = []
                price_plan['deductions'] = []

                for pc in price_components:

                    # Get initial information
                    price_component = {
                        'title': self._get_field(DCTERMS, pc, 'title')[0],
                        'description': self._get_field(DCTERMS, pc, 'description')[0]
                    }

                    # Check if it includes a price specification
                    price_specification = self._get_field(PRICE, pc, 'hasPrice', id_=True)[0]
                    function_found = False

                    if price_specification != '':
                        price_container = price_specification
                    else:
                        # Check if a price function exists
                        price_function = self._get_field(PRICE, pc, 'hasPriceFunction', id_=True)[0]
                        text_function = self._get_field(PRICE, pc, 'hasTextFunction')[0]

                        if price_function != '' and text_function != '':
                            function_found = True
                        else:
                            price_container = pc

                    if function_found:
                        # Save price function serialization
                        price_component['text_function'] = text_function
                        price_component['price_function'] = self._parse_function(price_function)
                    else:
                        # If not price function defined, get the price
                        price_component['currency'] = self._get_field(GR, price_container, 'hasCurrency')[0]
                        value = self._get_field(GR, price_container, 'hasCurrencyValue')[0]

                        if not value:
                            price_component['value'] = self._get_field(GR, price_container, 'hasValueFloat')[0]
                        else:
                            price_component['value'] = value

                        price_component['unit'] = self._get_field(GR, price_container, 'hasUnitOfMeasurement')[0]

                    # Check if it is a deduction getting component type
                    component_type = self._get_field(RDF, pc, 'type', id_=True)[0]

                    if component_type == PRICE['PriceComponent']:
                        price_plan['price_components'].append(price_component)
                    elif component_type == PRICE['Deduction']:
                        price_plan['deductions'].append(price_component)

            taxes = self._get_field(PRICE, price, 'hasTax', id_=True)

            if len(taxes) > 1 or taxes[0] != '':
                price_plan['taxes'] = []

                for pc in taxes:
                    tax = {
                        'title': self._get_field(DCTERMS, pc, 'title')[0],
                        'description': self._get_field(DCTERMS, pc, 'description')[0],
                        'currency': self._get_field(GR, pc, 'hasCurrency')[0],
                    }
                    value = self._get_field(GR, pc, 'hasCurrencyValue')

                    if not value:
                        tax['value'] = value[0]
                    else:
                        tax['value'] = self._get_field(GR, pc, 'hasValueFloat')[0]

                    tax['unit'] = self._get_field(GR, pc, 'hasUnitOfMeasurement')[0]
                    price_plan['taxes'].append(tax)

            result['price_plans'].append(price_plan)

        return result

    def parse(self):

        result = {}
        result['pricing'] = self._parse_pricing_info()
        result['services_included'] = []

        for service_uri in self._get_field(USDL, self._offering_uri, 'includes', id_=True):

            if service_uri != '':
                basic_info = self._parse_basic_info(service_uri)
                if not basic_info['part_ref']:
                    basic_info['legal'] = self._parse_legal_info(service_uri)
                    basic_info['sla'] = self._parse_sla_info(service_uri)
                    basic_info['interactions'] = self._parse_interaction_protocols(service_uri)
                    del(basic_info['part_ref'])

                result['services_included'].append(basic_info)

        if not len(result['services_included']) > 0:
            raise Exception('No services included')

        return result


def validate_usdl(usdl, mimetype, offering_data):

    valid = True
    reason = ''
    # Parse the USDL document
    try:
        parser = USDLParser(usdl, mimetype)
        parsed_document = parser.parse()
    except:
        valid = False
        reason = 'Malformed USDL'

    # Check that it contains only a service
    if valid:
        if len(parsed_document['services_included']) != 1:
            valid = False
            reason = 'Only a Service included in the offering is supported'

    # Check that if there are more than a price plan all of them contain a label
    update_plan = False
    updates = 0
    developer_plan = False
    developers = 0
    if valid and len(parsed_document['pricing']['price_plans']) > 1:
        labels = []
        for plan in parsed_document['pricing']['price_plans']:
            if not 'label' in plan:
                valid = False
                reason = 'A label is required if there are more than a price plan'
                break
            elif plan['label'].lower() == 'update':
                update_plan = True
                updates += 1
            elif plan['label'].lower() == 'developer':
                developer_plan = True
                developers += 1
            elif plan['label'].lower() in labels:
                valid = False
                reason = 'The price plan labels must be unique'
                break
            else:
                labels.append(plan['label'].lower())

    elif valid and len(parsed_document['pricing']['price_plans']) == 1\
    and 'label' in parsed_document['pricing']['price_plans'][0] \
    and parsed_document['pricing']['price_plans'][0]['label'].lower() == 'update':
        update_plan = True

    # Check that it contains at most an update plan and a developer plan
    if valid and update_plan and updates > 1:
        valid = False
        reason = 'Only an updating price plan is allowed'

    if valid and developer_plan and developers > 1:
        valid = False
        reason = 'Only a developers plan is allowed'
    
    # Check if an update plan has been defined in order to check if a previous version
    # exists. The update plan is not allowed if it is the first version of the offering
    if valid and update_plan:
        offerings = Offering.objects.count(owner_organization=offering_data['organization'], name=offering_data['name'])
        if offerings == 0:
            valid = False
            reason = 'It is not possible to define an updating plan without a previous version of the offering'

    # Validate price components
    if valid and 'price_components' in parsed_document['pricing']['price_plans'][0]:
        price_components = parsed_document['pricing']['price_plans'][0]['price_components']

        from wstore.charging_engine.models import Unit

        currencies = []
        for component in price_components:

            if not 'price_function' in component:
                # Validate currency
                if component['currency'] != 'EUR' and component['currency'] != 'GBP':
                    valid = False
                    reason = 'A price component contains and invalid or unsupported currency'
                    break
                else:
                    # Check that all price components has the same currency
                    if len(currencies) != 0 and (not component['currency'] in currencies):
                        valid = False
                        reason = 'All price components must use the same currency'
                    else:
                        currencies.append(component['currency'])

                # Validate unit
                units = Unit.objects.filter(name=component['unit'].lower())
                if len(units) == 0:
                    valid = False
                    reason = 'A price component contains an unsupported unit'
                    break

                # Validate value
                try:
                    float(component['value'])
                except:
                    valid = False
                    reason = 'A price component contains an invalid value'
                    break

    return (valid, reason)
