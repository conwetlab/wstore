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

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import render

from wstore.oauth2provider.provider import WstoreAuthorizationProvider
from wstore.store_commons.utils.http import build_error_response



provider = WstoreAuthorizationProvider()


@require_http_methods(['GET', 'POST'])
@login_required
def provide_authorization_code(request):

    params = dict(request.GET)
    
    if 'response_type' not in params:
        return build_error_response(request, 400, 'Missing parameter response_type in URL query')

    if 'client_id' not in params:
        return build_error_response(request, 400, 'Missing parameter client_id in URL query')

    if 'redirect_uri' not in params:
        return build_error_response(request, 400, 'Missing parameter redirect_uri in URL query')

    params = {
        'response_type': params['response_type'][0],
        'client_id': params['client_id'][0],
        'redirect_uri':params['redirect_uri'][0]
    }

    if request.method == 'GET':
        return render(request, 'oauth2provider/auth.html', {'app': provider.get_client(params['client_id'])})
    else:
        return provider.get_authorization_code(request.user, **params)


@require_POST
def provide_authorization_token(request):

    raw_data = dict(request.POST)

    data = {
        'client_id': raw_data['client_id'][0],
        'client_secret': raw_data['client_secret'][0],
        'grant_type': raw_data['grant_type'][0]
    }
    if 'refresh_token' in raw_data:
        data['refresh_token'] = raw_data['refresh_token'][0]
    else:
        data['code'] = raw_data['code'][0]
        data['redirect_uri'] = raw_data['redirect_uri'][0]

    return provider.get_token_from_post_data(data)
