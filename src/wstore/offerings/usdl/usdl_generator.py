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

from wstore.models import Context


class USDLGenerator():

    _allowed_formats = ('xml', 'n3', 'json-ld')

    def _validate_info(self, offering_info):
        # Validate USDL mandatory fields
        if 'description' not in offering_info or 'base_id' not in offering_info \
                or 'organization' not in offering_info or 'name' not in offering_info \
                or 'version' not in offering_info or 'image_url' not in offering_info \
                or 'created' not in offering_info or 'abstract' not in offering_info:

            raise ValueError('Invalid USDL info: Missing a required field')

        # Validate that description field is not empty
        if not offering_info['description']:
            raise ValueError('Invalid USDL info: Description field cannot be empty')

        # Validate legal fields
        if 'legal' in offering_info:
            if 'title' not in offering_info['legal'] or 'text' not in offering_info['legal']:
                raise ValueError('Invalid USDL info: Title and text fields are required if providing legal info')

            if not offering_info['legal']['title'] or not offering_info['legal']['text']:
                raise ValueError('Invalid USDL info: Title and text fields cannot be empty in legal info')

    def _validate_pricing(self, pricing_info):
        # Validate pricing fields
        if 'price_model' not in pricing_info:
            raise ValueError('Invalid USDL info: The pricing field must define a pricing model')

        if pricing_info['price_model'] != 'free' and pricing_info['price_model'] != 'single_payment':
            raise ValueError('Invalid USDL info: Invalid pricing model')

        if pricing_info['price_model'] == 'single_payment':
            if 'price' not in pricing_info:
                raise ValueError('Invalid USDL info: Missing price for single payment model')

            if not pricing_info['price']:
                raise ValueError('Invalid USDL info: Price cannot be empty in single payment models')

    def generate_offering_usdl(self, offering_info, format_='xml'):

        if format_ not in self._allowed_formats:
            raise ValueError('The specified format (' + format_ + ') is not a valid format')

        self._validate_info(offering_info)

        # Get the template
        usdl_template = loader.get_template('usdl/basic_offering_usdl_template.rdf')

        site = Context.objects.all()[0].site.domain

        offering_uri = urljoin(site, 'api/offering/offerings/' + offering_info['organization'] + '/' + offering_info['name'] + '/' + offering_info['version'])
        image_url = urljoin(site, offering_info['image_url'])

        context = {
            'offering_uri': offering_uri,
            'image_url': image_url,
            'name': offering_info['name'],
            'version': offering_info['version'],
            'description': offering_info['description'],
            'abstract': offering_info['abstract'],
            'created': offering_info['created'],
            'base_id': offering_info['base_id']
        }

        if 'legal' in offering_info:
            context['legal'] = True
            context['license_label'] = offering_info['legal']['title']
            context['license_description'] = offering_info['legal']['text']

        # Render the template
        usdl = usdl_template.render(TmplContext(context))

        # Return the usdl in the spified format
        if format_ != 'xml':
            graph = rdflib.Graph()
            graph.parse(data=usdl, format='application/rdf+xml')
            usdl = graph.serialize(format=format_, auto_compact=True)

        # Return the USDL document
        return usdl

    def generate_pricing(self, pricing_info):
        self._validate_pricing(pricing_info)
