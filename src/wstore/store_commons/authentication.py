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

from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from django.conf import settings

from wstore.store_commons.utils.http import build_response


class Http403(Exception):
    pass


def logout(request):

    django_logout(request)
    response = None

    if settings.OILAUTH:
        # Check if the logout request is originated in a different domain
        if 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
            allowed_origins = [
                'https://account.lab.fi-ware.eu',
                'https://cloud.lab.fi-ware.eu',
                'https://mashup.lab.fi-ware.eu']

            if origin in allowed_origins:
                headers = {
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Credentials': 'true'
                }
                response = build_response(request, 200, 'OK', headers=headers)

        else:
            # If using the FI-LAB authentication and it is not a cross domain
            # request redirect to the FI-LAB main page
            response = build_response(request, 200, 'OK')

    # If not using the FI-LAB authentication redirect to the login page
    else:
        url = '/login?next=/'
        response = HttpResponseRedirect(url)

    return response
