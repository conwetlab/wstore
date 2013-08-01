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

"""
FI-WARE IdM OAuth2 support.

This contribution adds support for FI-WARE IdM OAuth2 service. The settings
FIWARE_APP_ID and FIWARE_API_SECRET must be defined with the values
given by FI-WARE IdM application registration process.

Extended permissions are supported by defining FIWARE_EXTENDED_PERMISSIONS
setting, it must be a list of values to request.

By default account id and token expiration time are stored in extra_data
field, check OAuthBackend class for details on how to extend it.
"""
from urllib import urlencode
from urllib2 import HTTPError

from django.utils import simplejson
from django.conf import settings

from social_auth.utils import dsa_urlopen
from social_auth.backends import BaseOAuth2, OAuthBackend
from social_auth.exceptions import AuthFailed


# GitHub configuration
FIWARE_AUTHORIZATION_URL = 'https://idm.lab.fi-ware.eu/authorize'
FIWARE_ACCESS_TOKEN_URL = 'https://idm.lab.fi-ware.eu/token'
FIWARE_USER_DATA_URL = 'https://idm.lab.fi-ware.eu/user'



class FiwareBackend(OAuthBackend):
    """FI-WARE IdM OAuth authentication backend"""
    name = 'fiware'
    # Default extra data to store
    EXTRA_DATA = [
        ('nickName', 'username'),
    ]

    def get_user_id(self, details, response):
        """Return the user id, FI-WARE IdM only provides username as a unique
        identifier"""
        return response['nickName']

    def get_user_details(self, response):
        """Return user details from FI-WARE account"""
        return {'username': response.get('nickName'),
                'email': response.get('email') or '',
                'fullname': response.get('displayName') or ''}


class FiwareAuth(BaseOAuth2):
    """FI-WARE OAuth2 mechanism"""
    AUTHORIZATION_URL = FIWARE_AUTHORIZATION_URL
    ACCESS_TOKEN_URL = FIWARE_ACCESS_TOKEN_URL
    AUTH_BACKEND = FiwareBackend
    REDIRECT_STATE = False
    STATE_PARAMETER = False
    SETTINGS_KEY_NAME = 'FIWARE_APP_ID'
    SETTINGS_SECRET_NAME = 'FIWARE_API_SECRET'
    SCOPE_SEPARATOR = ','
    # Look at http://developer.github.com/v3/oauth/
    SCOPE_VAR_NAME = 'FIWARE_EXTENDED_PERMISSIONS'

    FIWARE_ORGANIZATION = getattr(settings, 'FIWARE_ORGANIZATION', None)

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = FIWARE_USER_DATA_URL + '?' + urlencode({
            'access_token': access_token
        })

        try:
            data = simplejson.load(dsa_urlopen(url))
        except ValueError:
            data = None

        return data


def fill_internal_user_info(*arg, **kwargs):

    # Update user info
    response = kwargs['response']
    roles = response['roles']
    wstore_roles = []

    for role in roles:
        wstore_roles.append(role['name'])

    # Check if the user is an admin
    if 'Manager' in wstore_roles and not kwargs['user'].is_staff:
        kwargs['user'].is_staff = True
        kwargs['user'].save()

    elif not 'Manager' in wstore_roles and kwargs['user'].is_staff:
        kwargs['user'].is_staff = False
        kwargs['user'].save()

    # Check if the user is a provider
    if 'Provider' in wstore_roles and not 'provider' in kwargs['user'].userprofile.roles:
        kwargs['user'].userprofile.roles.append('provider')
        kwargs['user'].userprofile.save()

    if not 'Provider' in wstore_roles and 'provider' in kwargs['user'].userprofile.roles:
        kwargs['user'].userprofile.roles.remove('provider')
        kwargs['user'].userprofile.save()

    # Check organizations info


# Backend definition
BACKENDS = {
    'fiware': FiwareAuth,
}
