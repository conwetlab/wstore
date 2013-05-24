# -*- coding: utf-8 -*-


from django.contrib.auth.decorators import login_required
from wstore.store_commons.utils.http import build_error_response
from django.views.decorators.http import require_GET, require_POST

from wstore.oauth2provider.provider import WstoreAuthorizationProvider


provider = WstoreAuthorizationProvider()


@require_GET
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
