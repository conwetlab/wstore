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

import json
from mock import MagicMock

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from wstore.admin import views
from wstore.models import Organization


class OrganizationChangeTestCase(TestCase):

    tags = ('fiware-ut-25',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        # Create testing request
        self.data = {
            'organization': 'test_org'
        }
        self.request = self.factory.put(
            '/administration/organizations/change',
            json.dumps(self.data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.request.user = self.user

    def test_organization_change(self):

        org = Organization.objects.create(
            name='test_org'
        )
        # Update user profile info
        self.user.userprofile.organizations.append({
            'organization': org.pk
        })
        self.user.userprofile.save()

        response = views.change_current_organization(self.request)
        self.user = User.objects.get(username='test_user')
        self.assertEquals(self.user.userprofile.current_organization.pk, org.pk)

        body_response = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(body_response['message'], 'OK')
        self.assertEquals(body_response['result'], 'correct')

    def test_organization_change_errors(self):

        errors = [
            'Not found',
            'Forbidden'
        ]
        for i in [0, 1]:
            if i == 1:
                Organization.objects.create(
                    name='test_org'
                )

            response = views.change_current_organization(self.request)

            body_response = json.loads(response.content)
            self.assertEquals(body_response['message'], errors[i])
            self.assertEquals(body_response['result'], 'error')
