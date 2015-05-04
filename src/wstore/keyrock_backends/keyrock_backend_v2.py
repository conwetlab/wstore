# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from urlparse import urljoin

from social_auth.backends import OAuthBackend
from django.conf import settings

from wstore.models import Organization


FIWARE_AUTHORIZATION_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/oauth2/authorize')
FIWARE_ACCESS_TOKEN_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/oauth2/token')


class FiwareBackend(OAuthBackend):
    name = 'fiware'
    # Default extra data to store
    EXTRA_DATA = [
        ('id', 'username'),
        ('id', 'uid'),
    ]

    def get_user_id(self, details, response):
        return response['id']

    def get_user_details(self, response):
        """Return user details from FI-WARE account"""
        return {'username': response.get('id'),
                'email': response.get('email') or '',
                'fullname': response.get('displayName') or ''}


def fill_internal_user_info(*arg, **kwargs):
    # Update user info
    response = kwargs['response']
    from wstore.social_auth_backend import _fill_user_info, _create_private_org, _create_organizations

    _fill_user_info(response, kwargs['user'], response['id'])
    user_org = _create_private_org(kwargs['user'], response['roles'])

    idm_organizations = []
    if 'organizations' in response:
        idm_organizations = response['organizations']

    _create_organizations(kwargs['user'], user_org, idm_organizations, 'id')
