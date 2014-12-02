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

from __future__ import unicode_literals

import os
import json

from django.http import HttpResponse
from django.conf import settings

from wstore.store_commons.utils.http import build_response, authentication_required
from wstore.store_commons.resource import Resource
from wstore.search.search_engine import SearchEngine
from wstore.models import Resource as WStore_resource
from wstore.models import Organization, Offering
from wstore.offerings.offerings_management import get_offering_info


class SearchEntry(Resource):

    @authentication_required
    def read(self, request, text):

        index_path = os.path.join(settings.BASEDIR, 'wstore')
        index_path = os.path.join(index_path, 'search')
        index_path = os.path.join(index_path, 'indexes')

        search_engine = SearchEngine(index_path)

        filter_ = request.GET.get('filter', None)
        action = request.GET.get('action', None)
        start = request.GET.get('start', None)
        limit = request.GET.get('limit', None)
        sort = request.GET.get('sort', None)

        state = request.GET.get('state', None)
        if state:
            if state == 'ALL':
                state = ['uploaded', 'published', 'deleted']
            else:
                state = state.split(',')

        # Check the filter value
        if filter_ and filter_ != 'published' and filter_ != 'provided' and filter_ != 'purchased':
            return build_response(request, 400, 'Invalid filter')

        if state and filter_ != 'provided':
            return build_response(request, 400, 'Invalid filters')

        if filter_ == 'provider' and not state:
            return build_response(request, 400, 'Invalid filters')

        count = False
        pagination = None
        # Check if the action is count
        if action != None:
            if action == 'count':
                count = True
            else:
                return build_response(request, 400, 'Invalid action')
        else:
            # Check pagination params (Only when action is none)
            if start != None and limit != None:
                pagination = {
                    'start': int(start),
                    'limit': int(limit)
                }
            elif (start != None and limit == None) or (start == None and limit != None):
                return build_response(request, 400, 'Missing pagination param')

            # Check sorting values
            if sort != None:
                if sort != 'date' and sort != 'popularity' and sort != 'name':
                    return build_response(request, 400, 'Invalid sorting')

        if not filter_ or filter_ == 'published':
            response = search_engine.full_text_search(request.user, text, count=count, pagination=pagination, sort=sort)

        elif filter_ == 'provided':
            response = search_engine.full_text_search(request.user, text, state=state, count=count, pagination=pagination, sort=sort)

        elif filter_ == 'purchased':
            response = search_engine.full_text_search(request.user, text, state=['purchased'], count=count, pagination=pagination, sort=sort)

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')


class SearchByResourceEntry(Resource):

    @authentication_required
    def read(self, request, org, name, version):
        # Get resource model
        try:
            organization = Organization.objects.get(name=org)
            resource = WStore_resource.objects.get(provider=organization, name=name, version=version)
        except:
            return build_response(request, 404, 'Resource not found')

        # Check resource state
        if resource.state == 'deleted':
            return build_response(request, 404, 'Resource not found')

        # Get offering where the resource is included
        response = []

        try:
            for off in resource.offerings:
                offering = Offering.objects.get(pk=off)
                response.append(get_offering_info(offering, request.user))
        except Exception as e:
            return build_response(request, 400, unicode(e))

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')