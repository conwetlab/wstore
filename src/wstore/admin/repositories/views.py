# -*- coding: utf-8 -*-

# Copyright (c) 2013-2015 CoNWeT Lab., Universidad Politécnica de Madrid

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
from django.core.exceptions import ObjectDoesNotExist

from wstore.store_commons.errors import ConflictError
from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.name import is_valid_id
from wstore.store_commons.utils.http import build_response, supported_request_mime_types,\
    authentication_required
from wstore.admin.repositories.repositories_management import register_repository, unregister_repository, \
    get_repositories, set_default_repository


class RepositoryCollection(Resource):

    # Register a new repository on the store
    # in order to be able to upload and
    # download resources
    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        if not request.user.is_staff:  # Only an admin could register a new repository
            return build_response(request, 403, 'Forbidden')

        # Get request info
        name = None
        host = None
        try:
            content = json.loads(request.raw_post_data)
            name = content['name']
            host = content['host']
            is_default = content.get('is_default', False)
        except:
            msg = "Request body is not valid JSON data"
            return build_response(request, 400, msg)

        # Check data formats
        if not is_valid_id(name):
            return build_response(request, 400, 'Invalid name format')

        if not is_valid_url(host):
            return build_response(request, 400, 'Invalid URL format')

        # Register repository
        try:
            register_repository(name, host, is_default)
        except ConflictError as e:
            return build_response(request, 409, unicode(e))
        except Exception as e:
            return build_response(request, 500, unicode(e))

        return build_response(request, 201, 'Created')

    @authentication_required
    def read(self, request):

        try:
            response = json.dumps(get_repositories())
        except:
            return build_response(request, 400, 'Invalid request')

        return HttpResponse(response, status=200, mimetype='application/JSON; charset=UTF-8')


def _manage_repository(user, repository, method):

    if not user.is_staff:
        return (True, 403, 'Forbidden')

    try:
        method(repository)
    except ObjectDoesNotExist as e:
        return (True, 404, unicode(e))
    except Exception as e:
        return (True, 500, 'Error managing the repository')

    return (False, None, None)


class RepositoryDefaultEntry(Resource):

    @authentication_required
    def create(self, request, repository):
        result = _manage_repository(request.user, repository, set_default_repository)
        if result[0]:
            return build_response(request, result[1], result[2])
        else:
            return build_response(request, 200, 'OK')


class RepositoryEntry(Resource):

    @authentication_required
    def delete(self, request, repository):

        result = _manage_repository(request.user, repository, unregister_repository)
        if result[0]:
            return build_response(request, result[1], result[2])
        else:
            return build_response(request, 204, 'No content')
