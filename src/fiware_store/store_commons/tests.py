
from django.test import TestCase

from fiware_store.store_commons.utils.usdlParser import USDLParser


class UsdlParserTestCase(TestCase):

    def test_basic_parse(self):

        f = open('./fiware_store/store_commons/test/basic_usdl.ttl', 'rb')

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
        f = open('./fiware_store/store_commons/test/test_usdl1.ttl', 'rb')

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
                self.assertEqual(price_com['value'], '1')
                self.assertEqual(price_com['currency'], 'euros')
                self.assertEqual(price_com['unit'], 'single pay')
            else:
                self.assertEqual(price_com['title'], 'Price component 2')
                self.assertEqual(price_com['description'], 'price component 2 description')
                self.assertEqual(price_com['value'], '1')
                self.assertEqual(price_com['currency'], 'euros')
                self.assertEqual(price_com['unit'], 'single pay')

        self.assertEqual(len(price_plan['taxes']), 1)
        self.assertEqual(price_plan['taxes'][0]['title'], 'Example tax')
        self.assertEqual(price_plan['taxes'][0]['description'], 'example tax description')
        self.assertEqual(price_plan['taxes'][0]['value'], '1')
        self.assertEqual(price_plan['taxes'][0]['currency'], 'euros')
        self.assertEqual(price_plan['taxes'][0]['unit'], 'percent')

    def test_parse_complete_service(self):

        f = open('./fiware_store/store_commons/test/test_usdl2.ttl', 'rb')

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
        self.assertEqual(sla[0]['slaExpresions'][0]['description'],'example service level description' )
        variables = sla[0]['slaExpresions'][0]['variables']
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0]['label'], 'Example variable')
        self.assertEqual(variables[0]['value'], 'example value')
        self.assertEqual(variables[0]['unit'], 'example unit')

    def test_parse_some_services(self):

        f = open('./fiware_store/store_commons/test/test_usdl3.ttl', 'rb')

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

        f = open('./fiware_store/store_commons/test/test_usdl4.ttl', 'rb')

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

    def test_parse_invalid_format(self):

        f = open('./fiware_store/store_commons/test/basic_usdl.ttl', 'rb')

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

        f = open('./fiware_store/store_commons/test/error_usdl1.ttl', 'rb')

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

        f = open('./fiware_store/store_commons/test/error_usdl2.ttl', 'rb')

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
