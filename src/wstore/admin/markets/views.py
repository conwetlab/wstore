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
from lxml import etree

from django.contrib.sites.models import get_current_site
from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_response, get_content_type, supported_request_mime_types,\
 authentication_required
from wstore.admin.markets.markets_management import get_marketplaces, register_on_market, unregister_from_market


class MarketplaceCollection(Resource):

    # Creates a new marketplace resource, that is
    # register the store in a marketplace and
    # add the marketplace info needed for access in
    # the database
    @authentication_required
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):
        if not request.user.is_staff:  # Only an admin could register the store in a marketplace
            return build_response(request, 401, 'Unautorized')

        content_type = get_content_type(request)[0]

        name = None
        host = None
        # Content types json and xml are supported
        if content_type == 'application/json':

            try:
                content = json.loads(request.raw_post_data)
                name = content['name']
                host = content['host']
            except:
                msg = "Request body is not valid JSON data"
                return build_response(request, 400, msg)

        else:

            try:
                content = etree.fromstring(request.raw_post_data)
                name = content.xpath('/marketplace/name')[0].text
                host = content.xpath('/marketplace/host')[0].text
            except:
                msg = "Request body is not a valid XML data"
                return build_response(request, 400, msg)

        try:
            register_on_market(name, host, get_current_site(request).domain)
        except Exception, e:
            if e.message == 'Bad Gateway':
                code = 502
                msg = e.message
            else:
                code = 400
                msg = 'Bad request'

            return build_response(request, code, msg)

        return build_response(request, 201, 'Created')

    @authentication_required
    def read(self, request):

        # Read Accept header to know the response mime type, JSON by default
        accept = request.META.get('ACCEPT', '')
        response = None
        mime_type = None

        result = get_marketplaces()
        if accept == '' or accept.find('application/JSON') > -1:
            response = json.dumps(result)
            mime_type = 'application/JSON; charset=UTF-8'

        elif accept.find('application/xml') > -1:
            root_elem = etree.Element('Marketplaces')

            for market in result:
                market_elem = etree.SubElement(root_elem, 'Marketplace')
                name_elem = etree.SubElement(market_elem, 'Name')
                name_elem.text = market['name']
                host_elem = etree.SubElement(market_elem, 'Host')
                host_elem.text = market['host']

            response = etree.tounicode(root_elem)
            mime_type = 'application/xml; charset=UTF-8'

        else:
            return build_response(request, 400, 'Invalid requested type')

        return HttpResponse(response, status=200, mimetype=mime_type)


class MarketplaceEntry(Resource):

    @authentication_required
    def read(self, request, market):
        pass

    @authentication_required
    def update(self, request, market):
        pass

    @authentication_required
    def delete(self, request, market):

        if not request.user.is_staff:
            return build_response(request, 401, 'Unathorized')

        try:
            unregister_from_market(market)
        except Exception, e:
            if e.message == 'Bad Gateway':
                code = 502
                msg = e.message
            else:
                if e.message == 'Not found':
                    code = 404
                    msg = e.message
                else:
                    code = 400
                    msg = 'Bad request'

            return build_response(request, code, msg)

        return build_response(request, 204, 'No content')
