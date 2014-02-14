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

from django.http import HttpResponse

from wstore.store_commons.utils.http import build_response, authentication_required
from wstore.store_commons.resource import Resource
from wstore.social.tagging.recommendation_manager import RecommendationManager
from wstore.social.tagging.tag_manager import TagManager
from wstore.models import Offering, Organization


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
                rec_man = RecommendationManager(offering)
                response = { 
                    'tags': rec_man.get_recommended_tags(tags)
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
    def update(self, request, organization, name, version):

        # Get offering
        try:
            org = Organization.objects.get(name=organization)
            offering = Offering.objects.get(owner_organization=org, name=name, version=version)
        except:
            return build_response(request, 404, 'Not found')

        # Build tag manager
        try:
            data = json.loads(request.raw_post_data)
            manager = TagManager()
            manager.update_tags(offering, data['tags'])
        except Exception, e:
            return build_response(request, 400, e.message)

        return build_response(request, 200, 'OK')
