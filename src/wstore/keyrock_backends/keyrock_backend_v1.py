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

import json
import urllib2
from urlparse import urljoin
from urllib2 import HTTPError

from social_auth.backends import OAuthBackend
from django.conf import settings

from wstore.store_commons.utils.method_request import MethodRequest


FIWARE_AUTHORIZATION_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/authorize')
FIWARE_ACCESS_TOKEN_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/token')
FIWARE_LOGOUT_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/users/sign_out')

FIWARE_NOTIFICATION_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/purchases')
FIWARE_APPLICATIONS_URL = urljoin(settings.FIWARE_IDM_ENDPOINT, '/applications.json')


class FiwareBackend(OAuthBackend):
    """FIWARE IdM OAuth authentication backend"""
    name = 'fiware'
    # Default extra data to store
    EXTRA_DATA = [
        ('nickName', 'username'),
        ('actorId', 'uid'),
    ]

    def get_user_id(self, details, response):
        """Return the user id, FI-WARE IdM only provides username as a unique
        identifier"""
        return response['actorId']

    def get_user_details(self, response):
        """Return user details from FI-WARE account"""
        return {'username': response.get('nickName'),
                'email': response.get('email') or '',
                'fullname': response.get('displayName') or ''}


def fill_internal_user_info(*arg, **kwargs):

    # Update user info
    response = kwargs['response']
    from wstore.social_auth_backend import _fill_user_info, _create_private_org, _create_organizations

    _fill_user_info(response, kwargs['user'], response['actorId'])
    user_org = _create_private_org(kwargs['user'], response['roles'])

    idm_organizations = []
    if 'organizations' in response:
        idm_organizations = response['organizations']

    _create_organizations(kwargs['user'], user_org, idm_organizations, 'actorId', 'displayName')


def _make_app_request(user, actor_id):

    token = user.userprofile.access_token

    url = FIWARE_APPLICATIONS_URL
    url += '?actor_id=' + str(actor_id)
    url += '&access_token=' + token

    req = MethodRequest('GET', url)

    # Call idm
    opener = urllib2.build_opener()

    resp = []
    response = opener.open(req)
    # Make the request
    resp = response.read()
    return resp


def get_applications(user):

    actor_id = user.userprofile.current_organization.actor_id

    try:
        _make_app_request(user, actor_id)

    except HTTPError as e:
        if e.code == 401:
            try:
                user.userprofile.refresh_token()
                resp = _make_app_request(user, actor_id)
            except:
                resp = json.dumps([])
        else:
            resp = json.dumps([])
    except:
        resp = json.dumps([])

    return resp


def notify_acquisition(purchase):

    data = {
        'applications': purchase.offering.applications
    }

    token = purchase.customer.userprofile.access_token
    body = json.dumps(data)
    headers = {'Content-type': 'application/json', 'Authorization': 'Bearer ' + token}

    request = MethodRequest('POST', FIWARE_NOTIFICATION_URL, body, headers)
    opener = urllib2.build_opener()

    try:
        opener.open(request)
    except HTTPError as e:
        if e.code == 401:
            try:
                purchase.customer.userprofile.refresh_token()
                token = purchase.customer.userprofile.access_token

                # Make the request
                headers = {'Content-type': 'application/json', 'Authorization': 'Bearer ' + token}
                request = MethodRequest('POST', FIWARE_NOTIFICATION_URL, body, headers)

                opener.open(request)
            except:
                pass
        else:
            pass
    except:
        pass
