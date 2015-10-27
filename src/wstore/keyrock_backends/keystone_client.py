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
import requests
from urlparse import urljoin


class KeystoneClient(object):

    _keystone_host = None
    _keystone_token = None
    _provider_role_id = None
    _purchaser_role_id = None

    def __init__(self, keystone_host, access_token, prov_id=None, pur_id=None):
        self._keystone_host = keystone_host
        self._keystone_token = self._get_keystone_token(access_token)
        self._provider_role_id = prov_id
        self._purchaser_role_id = pur_id

        if prov_id is None or pur_id is None:
            try:
                self._map_roles()
            except:
                self._provider_role_id = '106'
                self._purchaser_role_id = '191'

    def _get_keystone_token(self, access_token):
        """
            Changes an OAuth2 access token by a keystone token
            in order to access Keystone APIs
        """
        url = urljoin(self._keystone_host, 'v3/auth/tokens')

        data = {
            "auth": {
                "identity": {
                    "methods": [
                        "oauth2"
                    ],
                    "oauth2": {
                        'access_token_id': access_token
                    }
                }
            }
        }

        headers = {'Content-type': 'application/json'}
        resp = requests.post(url, data=json.dumps(data), headers=headers)

        resp.raise_for_status()

        # Get keystone token from headers
        return resp.headers['x-subject-token']

    def _make_request(self, url, method):
        headers = {
            'X-Auth-Token': self._keystone_token
        }

        resp = method(url, headers=headers)
        resp.raise_for_status()

        return resp

    def _map_roles(self):
        """
            Retrieves the id for the roles provider and purchaser
        """
        url = urljoin(self._keystone_host, 'v3/OS-ROLES/roles')
        resp = self._make_request(url, requests.get)

        # Search for the id of the provider and purchaser roles
        content = resp.json()['roles']

        found_prov = False
        found_pur = False
        i = 0
        while (not found_prov or not found_pur) and i < len(content):
            role = content[i]
            if role['is_internal'] and role['name'].lower() == 'provider':
                self._provider_role_id = role['id']
                found_prov = True

            elif role['is_internal'] and role['name'].lower() == 'purchaser':
                self._purchaser_role_id = role['id']
                found_pur = True
            i += 1

        if not found_pur or not found_pur:
            raise Exception('Required role not registered in Keystone instance')

    def get_app_info(self, app_id):
        """
            Retrieves the info of given app
        """
        url = urljoin(self._keystone_host, 'v3/OS-ROLES/consumers/' + app_id)
        resp = self._make_request(url, requests.get)

        content = resp.json()
        return {
            'id': app_id,
            'name': content['consumer']['name'],
            'url': content['consumer']['url'],
            'description': content['consumer']['description']
        }

    def _manage_apps(self, url, payload):

        headers = {
            'X-Auth-Token': self._keystone_token
        }

        resp = requests.get(url, params=payload, headers=headers)
        resp.raise_for_status()

        # Return apps where the user has the provider role
        content = resp.json()['role_assignments']
        apps = []
        for app in content:
            if app['role_id'] == self._provider_role_id:
                try:
                    apps.append(self.get_app_info(app['application_id']))
                except:
                    pass

        return apps

    def get_provider_apps(self, user_id):
        """
            Retrieves the applications belonging to the given user
        """
        url = urljoin(self._keystone_host, 'v3/OS-ROLES/users/role_assignments')
        payload = {
            'user_id': user_id,
            'default_organization': 'true'
        }

        return self._manage_apps(url, payload)

    def get_organization_apps(self, organization_id):
        """
            Retrieves the applications belonging to a given organization
        """
        url = urljoin(self._keystone_host, 'v3/OS-ROLES/organizations/role_assignments')
        payload = {
            'organization_id': organization_id
        }

        return self._manage_apps(url, payload)

    def _manage_purchaser_role(self, id_,  application_id, is_org, method):
        if is_org:
            path = 'v3/OS-ROLES/organizations' + id_ + '/applications/' + application_id + '/roles/' + self._purchaser_role_id
        else:
            path = 'v3/OS-ROLES/users/' + id_ + '/applications/' + application_id + '/roles/' + self._purchaser_role_id

        url = urljoin(self._keystone_host, path)
        self._make_request(url, method)

    def set_purchaser_role(self, id_, application_id, is_org=False):
        """
            Set the purchaser role to a given user in a given application
        """
        self._manage_purchaser_role(id_, application_id, is_org, requests.put)

    def remove_purchaser_role(self, id_, application_id, is_org=False):
        """
            Remove the purchaser role to a given user in a given application
        """
        self._manage_purchaser_role(id_, application_id, is_org, requests.delete)
