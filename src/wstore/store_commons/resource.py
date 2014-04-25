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

from django.http import Http404, HttpResponseNotAllowed, HttpResponseForbidden

from wstore.store_commons.authentication import Http403

METHOD_MAPPING = {
    'GET': 'read',
    'POST': 'create',
    'PUT': 'update',
    'DELETE': 'delete',
}


class Resource(object):

    def __init__(self, authentication=None, permitted_methods=None):

        self.permitted_methods = tuple([m.upper() for m in permitted_methods])

        for method in self.permitted_methods:
            if method not in METHOD_MAPPING or not callable(getattr(self, METHOD_MAPPING[method], None)):
                raise Exception('Missing method: ' + method)

    def __call__(self, request, *args, **kwargs):

        request_method = request.method.upper()
        if request_method not in self.permitted_methods:
            return HttpResponseNotAllowed(self.permitted_methods)

        try:
            return getattr(self, METHOD_MAPPING[request_method])(request, *args, **kwargs)
        except Http404:
            raise
        except Http403:
            return HttpResponseForbidden()
