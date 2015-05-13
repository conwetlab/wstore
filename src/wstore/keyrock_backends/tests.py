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
from mock import MagicMock
from nose_parameterized import parameterized
from requests.exceptions import HTTPError

from django.test import TestCase

from wstore.keyrock_backends import keyrock_backend_v1


class ApplicationsTestCase(TestCase):

    tags = ('applications', )

    def setUp(self):
        self.user = MagicMock()
        self.user.userprofile.current_organization.actor_id = 1
        self.user.userprofile.access_token = '111'
        keyrock_backend_v1.requests = MagicMock()
        self.mock_resp = MagicMock()
        self.mock_resp.text.return_value = json.dumps([{
            'id': 1,
            'url': 'http://exampleapp.com'
        }])
        keyrock_backend_v1.requests.get.return_value = self.mock_resp

    def tearDown(self):
        reload(keyrock_backend_v1)

    def _create_request_error(self, code):
        error = HTTPError()
        error.response = MagicMock()
        error.response.status_code = code
        keyrock_backend_v1.requests.get.side_effect = error

    def _inv_token(self):
        self._create_request_error(401)

    def _expired_token(self):

        def ref_token():
            self.user.userprofile.access_token = '222'

        self.user.userprofile.refreshing_token = ref_token

        def get_call(url, params=None):
            if params['access_token'] == '222':
                return self.mock_resp
            else:
                error = HTTPError()
                error.response = MagicMock()
                error.response.status_code = 401
                raise error

        keyrock_backend_v1.requests.get = get_call

    def _server_error(self):
        self._create_request_error(500)

    def _exception(self):
        keyrock_backend_v1._make_app_request = MagicMock()
        keyrock_backend_v1._make_app_request.side_effect = Exception('Error')

    @parameterized.expand([
        ('basic', [{
            'id': 1,
            'url': 'http://exampleapp.com'
        }]),
        ('invalid_token', [], _inv_token),
        ('refresh', [{
            'id': 1,
            'url': 'http://exampleapp.com'
        }], _expired_token),
        ('server_error', [], _server_error),
        ('exception', [], _exception)
    ])
    def test_get_applications_v1(self, name, expected, side_effect=None):

        if side_effect is not None:
            side_effect(self)

        resp = keyrock_backend_v1.get_applications(self.user)

        self.assertEquals(json.loads(resp), expected)
