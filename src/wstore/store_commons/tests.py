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
from mock import MagicMock

from django.test import TestCase

from wstore.store_commons.utils.usdlParser import USDLParser, validate_usdl
from wstore.models import Organization

__test__ = False


class UsdlParserTestCase(TestCase):

    tags = ('usdl-test-case',)

    def test_basic_parse(self):

        f = open('./wstore/store_commons/test/basic_usdl.ttl', 'rb')

        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 1)
        self.assertEqual(parsed_info['services_included'][0]['name'], 'example service')
        self.assertEqual(parsed_info['services_included'][0]['short_description'], 'Short description')
        self.assertEqual(parsed_info['services_included'][0]['long_description'], 'Long description')
        self.assertEqual(parsed_info['services_included'][0]['version'], '1.0')

    def test_parse_complete_offering(self):

        f = open('./wstore/store_commons/test/test_usdl1.ttl', 'rb')

        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 1)
        self.assertEqual(parsed_info['services_included'][0]['name'], 'example service')
        self.assertEqual(parsed_info['services_included'][0]['short_description'], 'Short description')
        self.assertEqual(parsed_info['services_included'][0]['long_description'], 'Long description')
        self.assertEqual(parsed_info['services_included'][0]['version'], '1.0')

        self.assertEqual(len(parsed_info['pricing']['price_plans']), 1)
        price_plan = parsed_info['pricing']['price_plans'][0]

        self.assertEqual(price_plan['title'], 'Example price plan')
        self.assertEqual(price_plan['description'], 'Price plan description')

        self.assertEqual(len(price_plan['price_components']), 2)

        for price_com in price_plan['price_components']:

            if price_com['title'] == 'Price component 1':
                self.assertEqual(price_com['title'], 'Price component 1')
                self.assertEqual(price_com['description'], 'price component 1 description')
                self.assertEqual(price_com['value'], '1.0')
                self.assertEqual(price_com['currency'], 'euros')
                self.assertEqual(price_com['unit'], 'single pay')
            else:
                self.assertEqual(price_com['title'], 'Price component 2')
                self.assertEqual(price_com['description'], 'price component 2 description')
                self.assertEqual(price_com['value'], '1.0')
                self.assertEqual(price_com['currency'], 'euros')
                self.assertEqual(price_com['unit'], 'single pay')

        self.assertEqual(len(price_plan['taxes']), 1)
        self.assertEqual(price_plan['taxes'][0]['title'], 'Example tax')
        self.assertEqual(price_plan['taxes'][0]['description'], 'example tax description')
        self.assertEqual(price_plan['taxes'][0]['value'], '1.0')
        self.assertEqual(price_plan['taxes'][0]['currency'], 'euros')
        self.assertEqual(price_plan['taxes'][0]['unit'], 'percent')

    def test_parse_complete_service(self):

        f = open('./wstore/store_commons/test/test_usdl2.ttl', 'rb')

        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 1)
        self.assertEqual(parsed_info['services_included'][0]['name'], 'example service')
        self.assertEqual(parsed_info['services_included'][0]['short_description'], 'Short description')
        self.assertEqual(parsed_info['services_included'][0]['long_description'], 'Long description')
        self.assertEqual(parsed_info['services_included'][0]['version'], '1.0')

        legal = parsed_info['services_included'][0]['legal']
        self.assertEqual(len(legal), 1)
        self.assertEqual(legal[0]['label'], 'example legal')
        self.assertEqual(legal[0]['description'], 'example legal description')

        self.assertEqual(len(legal[0]['clauses']), 2)

        for clause in legal[0]['clauses']:

            if clause['name'] == 'example clause 1':
                self.assertEqual(clause['name'], 'example clause 1')
                self.assertEqual(clause['text'], 'example text 1')
            else:
                self.assertEqual(clause['name'], 'example clause 2')
                self.assertEqual(clause['text'], 'example text 2')

        sla = parsed_info['services_included'][0]['sla']
        self.assertEqual(len(sla), 1)
        self.assertEqual(sla[0]['name'], 'example service level')
        self.assertEqual(len(sla[0]['slaExpresions']), 1)
        self.assertEqual(sla[0]['slaExpresions'][0]['description'], 'example service level description')
        variables = sla[0]['slaExpresions'][0]['variables']
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0]['label'], 'Example variable')
        self.assertEqual(variables[0]['value'], 'example value')
        self.assertEqual(variables[0]['unit'], 'example unit')

    def test_parse_some_services(self):

        f = open('./wstore/store_commons/test/test_usdl3.ttl', 'rb')

        parser = USDLParser(f.read(), 'text/turtle')
        f.close()
        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 2)

        for serv in parsed_info['services_included']:

            if serv['name'] == 'Example service 1':
                self.assertEqual(serv['name'], 'Example service 1')
                self.assertEqual(serv['short_description'], 'Short description 1')
                self.assertEqual(serv['long_description'], 'Long description 1')
                self.assertEqual(serv['version'], '1.0')
            else:
                self.assertEqual(serv['name'], 'Example service 2')
                self.assertEqual(serv['short_description'], 'Short description 2')
                self.assertEqual(serv['long_description'], 'Long description 2')
                self.assertEqual(serv['version'], '1.0')

    def test_parse_interaction_protocols(self):

        f = open('./wstore/store_commons/test/test_usdl4.ttl', 'rb')

        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 1)
        self.assertEqual(parsed_info['services_included'][0]['name'], 'Example service')
        self.assertEqual(parsed_info['services_included'][0]['short_description'], 'Short description')
        self.assertEqual(parsed_info['services_included'][0]['long_description'], 'Long description')

        interactions = parsed_info['services_included'][0]['interactions']

        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0]['title'], 'test protocol')
        self.assertEqual(interactions[0]['description'], 'test protocol description')
        self.assertEqual(interactions[0]['technical_interface'], 'http://technicalinterface.com')

        inter = interactions[0]['interactions']

        self.assertEqual(len(inter), 1)
        self.assertEqual(inter[0]['title'], 'test interaction')
        self.assertEqual(inter[0]['description'], 'test interaction description')
        self.assertEqual(inter[0]['interface_operation'], 'http://interfaceoperation.com')

        inputs = inter[0]['inputs']

        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0]['label'], 'test input')
        self.assertEqual(inputs[0]['description'], 'test input description')
        self.assertEqual(inputs[0]['interface_element'], 'http://interfaceelementinput.com')

        outputs = inter[0]['outputs']

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0]['label'], 'test output')
        self.assertEqual(outputs[0]['description'], 'test output description')
        self.assertEqual(outputs[0]['interface_element'], 'http://interfaceelementoutput.com')

    def test_parse_price_specification(self):

        f = open('./wstore/store_commons/test/test_usdl5.ttl', 'rb')
        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 1)
        self.assertEqual(parsed_info['services_included'][0]['name'], 'example service')
        self.assertEqual(parsed_info['services_included'][0]['short_description'], 'Short description')
        self.assertEqual(parsed_info['services_included'][0]['long_description'], 'Long description')
        self.assertEqual(parsed_info['services_included'][0]['version'], '1.0')

        self.assertEqual(len(parsed_info['pricing']['price_plans']), 1)
        price_plan = parsed_info['pricing']['price_plans'][0]

        self.assertEqual(price_plan['title'], 'Example price plan')
        self.assertEqual(price_plan['description'], 'Price plan description')

        self.assertEqual(len(price_plan['price_components']), 2)

        for price_com in price_plan['price_components']:

            if price_com['title'] == 'Price component 1':
                self.assertEqual(price_com['title'], 'Price component 1')
                self.assertEqual(price_com['description'], 'price component 1 description')
                self.assertEqual(price_com['value'], '1.0')
                self.assertEqual(price_com['currency'], 'EUR')
                self.assertEqual(price_com['unit'], 'single pay')
            else:
                self.assertEqual(price_com['title'], 'Price component 2')
                self.assertEqual(price_com['description'], 'price component 2 description')
                self.assertEqual(price_com['value'], '1.0')
                self.assertEqual(price_com['currency'], 'EUR')
                self.assertEqual(price_com['unit'], 'single pay')

        self.assertEqual(len(price_plan['taxes']), 1)
        self.assertEqual(price_plan['taxes'][0]['title'], 'Example tax')
        self.assertEqual(price_plan['taxes'][0]['description'], 'example tax description')
        self.assertEqual(price_plan['taxes'][0]['value'], '1.0')
        self.assertEqual(price_plan['taxes'][0]['currency'], 'EUR')
        self.assertEqual(price_plan['taxes'][0]['unit'], 'percent')

    def test_parse_price_deductions(self):

        f = open('./wstore/store_commons/test/test_usdl6.ttl', 'rb')
        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        parsed_info = parser.parse()

        self.assertEqual(parsed_info['pricing']['title'], 'test offering')
        self.assertEqual(len(parsed_info['services_included']), 1)
        self.assertEqual(parsed_info['services_included'][0]['name'], 'example service')
        self.assertEqual(parsed_info['services_included'][0]['short_description'], 'Short description')
        self.assertEqual(parsed_info['services_included'][0]['long_description'], 'Long description')
        self.assertEqual(parsed_info['services_included'][0]['version'], '1.0')

        self.assertEqual(len(parsed_info['pricing']['price_plans']), 1)
        price_plan = parsed_info['pricing']['price_plans'][0]

        self.assertEqual(price_plan['title'], 'Example price plan')
        self.assertEqual(price_plan['description'], 'Price plan description')

        self.assertEqual(len(price_plan['price_components']), 1)
        self.assertEqual(len(price_plan['deductions']), 1)

        price_com = price_plan['price_components'][0]
        self.assertEqual(price_com['title'], 'Price component')
        self.assertEqual(price_com['description'], 'price component description')
        self.assertEqual(price_com['value'], '1.0')
        self.assertEqual(price_com['currency'], 'EUR')
        self.assertEqual(price_com['unit'], 'single pay')

        deduction = price_plan['deductions'][0]
        self.assertEqual(deduction['title'], 'Price deduction')
        self.assertEqual(deduction['description'], 'price deduction description')
        self.assertEqual(deduction['value'], '1.0')
        self.assertEqual(deduction['currency'], 'EUR')
        self.assertEqual(deduction['unit'], 'single pay')

        self.assertEqual(len(price_plan['taxes']), 1)
        self.assertEqual(price_plan['taxes'][0]['title'], 'Example tax')
        self.assertEqual(price_plan['taxes'][0]['description'], 'example tax description')
        self.assertEqual(price_plan['taxes'][0]['value'], '1.0')
        self.assertEqual(price_plan['taxes'][0]['currency'], 'EUR')
        self.assertEqual(price_plan['taxes'][0]['unit'], 'percent')

    test_parse_price_deductions.tags = ('fiware-ut-27',)

    def test_parse_invalid_format(self):

        f = open('./wstore/store_commons/test/basic_usdl.ttl', 'rb')

        error = False
        msg = None
        try:
            parser = USDLParser(f.read(), 'text/fail')
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Error the document has not a valid rdf format')
        f.close()

    def test_parse_no_offering(self):

        f = open('./wstore/store_commons/test/error_usdl1.ttl', 'rb')

        error = False
        msg = None
        try:
            parser = USDLParser(f.read(), 'text/turtle')
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'No service offering has been defined')
        f.close()

    def test_parse_no_services(self):

        f = open('./wstore/store_commons/test/error_usdl2.ttl', 'rb')

        parser = USDLParser(f.read(), 'text/turtle')
        f.close()

        error = False
        msg = None
        try:
            parser.parse()
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'No services included')


class USDLValidationTestCase(TestCase):

    tags = ('usdl-validation',)

    def test_basic_validation(self):
        f = open('./wstore/store_commons/test/val.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertTrue(valid[0])

    def test_validate_price_components(self):
        f = open('./wstore/store_commons/test/val_comp.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertTrue(valid[0])

    def test_validate_invalid_service(self):
        f = open('./wstore/store_commons/test/val_serv.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'Only a Service included in the offering is supported')

    def test_validate_invalid_price_plan(self):

        from wstore.store_commons.utils import usdlParser
        usdlParser.USDLParser = MagicMock()
        parser = MagicMock()
        parser.parse.return_value = {
            'services_included': ['service'],
            'pricing': {
                'price_plans': [{
                    'title': 'plan 1',
                },{
                    'title': 'plan 2',
                }]
            }
        }
        usdlParser.USDLParser.return_value = parser
        valid = usdlParser.validate_usdl('', 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'A label is required if there are more than a price plan')

        parser.parse.return_value = {
            'services_included': ['service'],
            'pricing': {
                'price_plans': [{
                    'title': 'plan 1',
                    'label': 'plan_label'
                },{
                    'title': 'plan 2',
                    'label': 'plan_label'
                }]
            }
        }
        usdlParser.USDLParser.return_value = parser
        valid = usdlParser.validate_usdl('', 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'The price plan labels must be unique')


        parser.parse.return_value = {
            'services_included': ['service'],
            'pricing': {
                'price_plans': [{
                    'title': 'plan 1',
                    'label': 'update'
                },{
                    'title': 'plan 2',
                    'label': 'update'
                }]
            }
        }
        usdlParser.USDLParser.return_value = parser
        valid = usdlParser.validate_usdl('', 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'Only an updating price plan is allowed')

        parser.parse.return_value = {
            'services_included': ['service'],
            'pricing': {
                'price_plans': [{
                    'title': 'plan 1',
                    'label': 'developer'
                },{
                    'title': 'plan 2',
                    'label': 'developer'
                }]
            }
        }
        usdlParser.USDLParser.return_value = parser
        valid = usdlParser.validate_usdl('', 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'Only a developers plan is allowed')

        parser.parse.return_value = {
            'services_included': ['service'],
            'pricing': {
                'price_plans': [{
                    'title': 'plan 1',
                    'label': 'update'
                },{
                    'title': 'plan 2',
                    'label': 'developer'
                }]
            }
        }
        usdlParser.USDLParser.return_value = parser
        org = Organization.objects.create(name='org')
        valid = usdlParser.validate_usdl('', 'text/turtle', {'organization': org, 'name': 'offering'})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'It is not possible to define an updating plan without a previous version of the offering')

        usdlParser.USDLParser = USDLParser

    def test_validate_invalid_currency(self):
        f = open('./wstore/store_commons/test/val_curr.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'A price component contains and invalid or unsupported currency')

    def test_validate_multiple_currencies(self):
        f = open('./wstore/store_commons/test/val_mul_curr.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'All price components must use the same currency')

    def test_validate_invalid_unit(self):
        f = open('./wstore/store_commons/test/val_unit.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'A price component contains an unsupported unit')

    def test_validate_invalid_value(self):
        f = open('./wstore/store_commons/test/val_value.ttl', 'rb')
        valid = validate_usdl(f.read(), 'text/turtle', {})

        self.assertFalse(valid[0])
        self.assertEquals(valid[1], 'A price component contains an invalid value')


class FakeParser(USDLParser):

    def __init__(self, graph):
        self._graph = graph


class PriceFunctionParsingTestCase(TestCase):

    tags = ('usdl-price-func', 'fiware-ut-27')

    def test_price_function_parsing(self):

        # Load price function RDF
        f = open('wstore/store_commons/test/price_funct_pars.ttl', 'rb')
        g = rdflib.Graph().parse(data=f.read(), format='n3')
        # Get price function node
        price_function = g.subjects(rdflib.RDF.type, rdflib.URIRef('http://spinrdf.org/spin#Function')).next()

        # Avoid constructor checks, not needed for the current test
        # USDLParser.__init__ = fake_init
        usdl_parser = FakeParser(g)
        parsed_function = usdl_parser._parse_function(price_function)

        # Check parsed function
        self.assertEquals(len(parsed_function['variables']), 2)
        self.assertEquals(parsed_function['variables']['usage']['label'], 'Usage variable')
        self.assertEquals(parsed_function['variables']['usage']['type'], 'usage')
        self.assertEquals(parsed_function['variables']['constant']['label'], 'Constant')
        self.assertEquals(parsed_function['variables']['constant']['type'], 'constant')

        self.assertEquals(parsed_function['function']['operation'], '+')
        self.assertEquals(parsed_function['function']['arg1'], 'usage')
        self.assertEquals(parsed_function['function']['arg2']['operation'], '*')
        self.assertEquals(parsed_function['function']['arg2']['arg1']['operation'], '*')
        self.assertEquals(parsed_function['function']['arg2']['arg1']['arg1'], 'constant')
        self.assertEquals(parsed_function['function']['arg2']['arg1']['arg2'], 'constant')
        self.assertEquals(parsed_function['function']['arg2']['arg2'], 'usage')

    def test_price_function_exceptions(self):

        # Load testing info
        usdls = [
            'wstore/store_commons/test/price_funct_err1.ttl',
            'wstore/store_commons/test/price_funct_err2.ttl',
            'wstore/store_commons/test/price_funct_err3.ttl',
            'wstore/store_commons/test/price_funct_err4.ttl',
            'wstore/store_commons/test/price_funct_err5.ttl',
            'wstore/store_commons/test/price_funct_err6.ttl',
            'wstore/store_commons/test/price_funct_err7.ttl',
            'wstore/store_commons/test/price_funct_err8.ttl',
            'wstore/store_commons/test/price_funct_err9.ttl',
            'wstore/store_commons/test/price_funct_err10.ttl'
        ]
        error_messages = [
            'Only a value is allowed for constants',
            'Invalid variable type',
            'Invalid SPARQL method',
            'Only a bind expression is allowed',
            'Variable not declared',
            'Duplicated expression',
            'Duplicated expression',
            'Invalid predicate',
            'An expression must contain an operation per level',
            'Invalid operation'
        ]
        # Test all exceptions that can be raised
        for i in range(0, 9):
            # Load price function RDF
            f = open(usdls[i], 'rb')
            g = rdflib.Graph().parse(data=f.read(), format='n3')
            # Get price function node
            price_function = g.subjects(rdflib.RDF.type, rdflib.URIRef('http://spinrdf.org/spin#Function')).next()

            # Avoid constructor checks, not needed for the current test
            # USDLParser.__init__ = fake_init
            usdl_parser = FakeParser(g)

            error = False
            msg = None
            try:
                usdl_parser._parse_function(price_function)
            except Exception, e:
                error = True
                msg = e.message

            self.assertTrue(error)
            self.assertEquals(msg, 'Invalid price function: ' + error_messages[i])
