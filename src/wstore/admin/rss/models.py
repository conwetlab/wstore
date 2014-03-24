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

from django.db import models
from djangotoolbox.fields import ListField, DictField


class RSS(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=500)
    expenditure_limits = DictField()
    correlation_number = models.IntegerField(default=0)
    pending_cdrs = ListField()
    in_use = models.BooleanField(default=False)
    # Not all users of the store are authorized to access the RSS
    # so a valid access access token and refresh token are stored
    # when the RSS info is created
    access_token = models.CharField(max_length=150, null=True, blank=True)
    refresh_token = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        app_label = 'wstore'

    def refresh_token(self):
        """
        Refresh the access token used for accessing the RSS
        """
        from wstore.models import UserProfile
        # Get user
        userprofile = UserProfile.objects.get(access_token=self.access_token)
        # Refresh token
        social = userprofile.user.social_auth.filter(provider='fiware')[0]
        social.refresh_token()

        social = userprofile.user.social_auth.filter(provider='fiware')[0]
        credentials = social.extra_data

        # Save new credentials
        userprofile.access_token = credentials['access_token']
        userprofile.refresh_token = credentials['refresh_token']
        userprofile.save()

        self.access_token = credentials['access_token']
        self.save()
