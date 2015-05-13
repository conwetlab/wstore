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

from djangotoolbox.fields import EmbeddedModelField

from django.db import models


class MarketCredentials(models.Model):
    username = models.CharField(max_length=30, blank=True, null=True)
    passwd = models.CharField(max_length=50, blank=True, null=True)


class Marketplace(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=100)
    api_version = models.IntegerField(default=1)
    store_id = models.CharField(max_length=100)
    credentials = EmbeddedModelField(MarketCredentials)

    class Meta:
        app_label = 'wstore'
