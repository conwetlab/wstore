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

from django.contrib.sites.models import get_current_site
from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.name import is_valid_id
from wstore.store_commons.utils.http import build_response, supported_request_mime_types,\
 authentication_required
from wstore.admin.markets.markets_management import get_marketplaces, register_on_market, unregister_from_market


class MarketplaceCollection(Resource):

    # Creates a new marketplace resource, that is
    # register the store in a marketplace and
    # add the marketplace info needed for access in
    # the database
    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):
        if not request.user.is_staff:  # Only an admin could register the store in a marketplace
            return build_response(request, 403, 'Forbidden')

        name = None
        host = None

        # Get contents from the request
        try:
            content = json.loads(request.raw_post_data)
            name = content['name']
            host = content['host']
        except:
            msg = "Request body is not valid JSON data"
            return build_response(request, 400, msg)

        # Check data formats
        if not is_valid_id(name):
            return build_response(request, 400, 'Invalid name format')

        if not is_valid_url(host):
            return build_response(request, 400, 'Invalid URL format')
        
        code = 201
        msg = 'Created'
        try:
            # Register the store in the selected marketplace
            register_on_market(name, host, get_current_site(request).domain)
        except Exception, e:
            if e.message == 'Bad Gateway':
                code = 502
                msg = e.message
            else:
                code = 400
                msg = 'Bad request'

        return build_response(request, code, msg)

    @authentication_required
    def read(self, request):

        try:
            response = json.dumps(get_marketplaces())
        except:
            return build_response(request, 400, 'Invalid request')

        return HttpResponse(response, status=200, mimetype='application/JSON; charset=UTF-8')


class MarketplaceEntry(Resource):

    @authentication_required
    def delete(self, request, market):

        if not request.user.is_staff:
            return build_response(request, 403, 'Forbidden')

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
