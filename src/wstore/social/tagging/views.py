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

import json

from django.http import HttpResponse

from wstore.store_commons.utils.http import build_response, authentication_required, supported_request_mime_types
from wstore.store_commons.resource import Resource
from wstore.social.tagging.recommendation_manager import RecommendationManager
from wstore.social.tagging.tag_manager import TagManager
from wstore.models import Offering, Organization
from wstore.offerings.offerings_management import get_offering_info


class TagCollection(Resource):

    @authentication_required
    def read(self, request, organization, name, version):
        # Get offering
        try:
            org = Organization.objects.get(name=organization)
            offering = Offering.objects.get(owner_organization=org, name=name, version=version)
        except:
            return build_response(request, 404, 'Not found')

        # Check if is a tagging recommendation or a tags request
        action = request.GET.get('action', None)

        if action:
            if action == 'recommend':
                # Get user tags
                tags = request.GET.get('tags', '')

                # Split tags
                tags = set(tags.split(','))

                # Get recommended tags
                rec_man = RecommendationManager(offering, tags)
                response = { 
                    'tags': [tag for tag, r in rec_man.get_recommended_tags()]
                }
            else:
                return build_response(request, 400, 'Invalid action')

        else:
            response = {
                'tags': offering.tags
            }
        # Build response
        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, organization, name, version):

        # Get offering
        try:
            org = Organization.objects.get(name=organization)
            offering = Offering.objects.get(owner_organization=org, name=name, version=version)
        except:
            return build_response(request, 404, 'Not found')

        # Check that the user has enough rights
        if request.user.userprofile.current_organization != org\
        or (not offering.is_owner(request.user) and not request.user.pk in org.managers):
            return build_response(request, 403, 'Forbidden')

        # Build tag manager
        try:
            data = json.loads(request.raw_post_data)
            manager = TagManager()
            manager.update_tags(offering, data['tags'])
        except Exception, e:
            return build_response(request, 400, e.message)

        return build_response(request, 200, 'OK')

class SearchTagEntry(Resource):

    @authentication_required
    def read(self, request, tag):
        # Get query params
        action = request.GET.get('action', None)
        start = request.GET.get('start', None)
        limit = request.GET.get('limit', None)
        sort = request.GET.get('sort', None)
        state = request.GET.get('filter', None)

        # Check action format
        if action and not (isinstance(action,str) or isinstance(action,unicode)):
            return build_response(request, 400, 'Invalid action format')

        # Validate action
        if action and action != 'count':
            return build_response(request, 400, 'Invalid action')

        if action and (start or limit or sort):
            return build_response(request, 400, 'Actions cannot be combined with pagination')

        # Validate pagination
        if (start and not limit) or (not start and limit):
            return build_response(request, 400, 'Both pagination params are required')

        if start and limit and (not start.isnumeric() or not limit.isnumeric()):
            return build_response(request, 400, 'Invalid format in pagination parameters')
        elif start and limit:
            start = int(start)
            limit = int(limit)

        if start and limit and (start < 1 or limit < 1):
            return build_response(request, 400, 'Pagination params must be equal or greater that 1')

        # Validate sorting
        allowed_sorting = ['name', 'date', 'popularity']
        if sort and (not isinstance(sort, str) and not isinstance(sort, unicode)):
            return build_response(request, 400, 'Invalid sorting format')

        if sort and not sort in allowed_sorting:
            return build_response(request, 400, 'Invalid sorting value')

        # Validate state
        if state and state != 'published' and state != 'purchased':
            return build_response(request, 400, 'Invalid filter')

        try:
            # Build tag manager
            tm = TagManager()

            # Select action
            if action == 'count':
                response = {
                    'number': tm.count_offerings(tag)
                }
            else:
                offerings = tm.search_by_tag(tag)

                response = []
                # Get offering info
                for off in offerings:
                    offering_info = get_offering_info(off, request.user)

                    if not state and offering_info['state'] != 'published'\
                    and offering_info['state'] != 'purchased' and offering_info['state'] != 'rated':
                        continue

                    response.append(offering_info)

                # Sort offerings if needed
                if sort:
                    rev = True
                    if sort == 'name':
                        rev = False
                    elif sort == 'date':
                        sort = 'publication_date'
                    elif sort == 'popularity':
                        sort = 'rating'

                    response = sorted(response, key=lambda off: off[sort], reverse=rev)

                # If sort was needed pagination must be done after sorting
                if start and limit:
                    response = response[start - 1: (limit + (start - 1))]

        except Exception as e:
            return build_response(request, 400, unicode(e))

        # Create response
        return HttpResponse(json.dumps(response), status=200, mimetype='application/json; charset=utf-8')
