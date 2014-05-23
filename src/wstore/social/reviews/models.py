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

from django.contrib.auth.models import User
from django.db import models
from djangotoolbox.fields import EmbeddedModelField

from wstore.models import Organization, Offering

# Review responses (Embedded)
class Response(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)
    timestamp = models.DateTimeField()
    title = models.CharField(max_length=60)
    response = models.TextField(max_length=200)


# User reviews of offerings
class Review(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)
    offering = models.ForeignKey(Offering)
    timestamp = models.DateTimeField()
    title = models.CharField(max_length=60)
    comment = models.TextField(max_length=200)
    rating = models.IntegerField(default=0)
    response = EmbeddedModelField(Response, null=True)

    class Meta:
        app_label = 'wstore'
        unique_together = ('user', 'organization', 'offering')

    