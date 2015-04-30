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

from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from django.conf import settings

from wstore.store_commons.utils.http import build_response
from wstore.store_commons.utils.url import add_slash


class Http403(Exception):
    pass


def logout(request):

    django_logout(request)
    response = None

    if settings.PORTALINSTANCE:
        # Check if the logout request is originated in a different domain
        if 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
            origin = add_slash(origin)

            from wstore.views import ACCOUNT_PORTAL_URL, CLOUD_PORTAL_URL, MASHUP_PORTAL_URL, DATA_PORTAL_URL

            allowed_origins = [
                add_slash(ACCOUNT_PORTAL_URL),
                add_slash(CLOUD_PORTAL_URL),
                add_slash(MASHUP_PORTAL_URL),
                add_slash(DATA_PORTAL_URL)
            ]

            if origin in allowed_origins:
                headers = {
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Credentials': 'true'
                }
                response = build_response(request, 200, 'OK', headers=headers)
            else:
                response = build_response(request, 403, 'Forbidden')

        else:
            # If using the FI-LAB authentication and it is not a cross domain
            # request redirect to the FI-LAB main page
            response = build_response(request, 200, 'OK')

    # If not using the FI-LAB authentication redirect to the login page
    elif settings.OILAUTH:
        from wstore.social_auth_backend import FIWARE_LOGOUT_URL
        response = HttpResponseRedirect(FIWARE_LOGOUT_URL)
    else:
        url = '/login?next=/'
        response = HttpResponseRedirect(url)

    return response
