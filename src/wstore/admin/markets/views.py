# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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
from urllib2 import HTTPError

from django.contrib.sites.models import get_current_site
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.conf import settings

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

        if not request.user.is_staff:  # Only an admin can register the store in a marketplace
            return build_response(request, 403, 'You are not allowed to register WStore in a Marketplace')

        name = None
        host = None
        api_version = None

        # Get contents from the request
        try:
            content = json.loads(request.raw_post_data)
            name = content['name']
            host = content['host']
            api_version = content['api_version']
        except:
            msg = "Request body is not valid JSON data"
            return build_response(request, 400, msg)

        # Check data formats
        if not is_valid_id(name):
            return build_response(request, 400, 'Invalid name format')

        if not is_valid_url(host):
            return build_response(request, 400, 'Invalid URL format')

        if not api_version.isdigit():
            return build_response(request, 400, 'Invalid API version')

        api_version = int(api_version)

        if api_version != 1 and api_version != 2:
            return build_response(request, 400, 'Invalid API version')

        credentials = None
        # Validate credentials if required
        if api_version == 1 or not settings.OILAUTH:
            if 'credentials' not in content:
                return build_response(request, 400, 'Missing required field credentials')

            if 'username' not in content['credentials']:
                return build_response(request, 400, 'Missing required field username in credentials')

            if 'passwd' not in content['credentials']:
                return build_response(request, 400, 'Missing required field passwd in credentials')

            credentials = content['credentials']

        code = 201
        msg = 'Created'
        try:
            # Register the store in the selected marketplace
            register_on_market(request.user, name, host, api_version, credentials, get_current_site(request).domain)
        except HTTPError:
            code = 502
            msg = "The Marketplace has failed registering the store"
        except PermissionDenied as e:
            code = 403
            msg = unicode(e)
        except Exception as e:
            code = 500
            msg = unicode(e)

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
            unregister_from_market(request.user, market)
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
