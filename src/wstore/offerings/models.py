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
from djangotoolbox.fields import ListField, DictField

from wstore.models import Marketplace
from wstore.models import Organization


# An application is an offering composed by some
# backend comopents and some resources
class Offering(models.Model):
    name = models.CharField(max_length=50)
    owner_organization = models.ForeignKey(Organization)
    owner_admin_user = models.ForeignKey(User)
    # support_organization
    # support_admin_user
    version = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    description_url = models.CharField(max_length=200)
    marketplaces = ListField(models.ForeignKey(Marketplace))
    resources = ListField()
    rating = models.FloatField(default=0)
    comments = ListField()
    tags = ListField()
    image_url = models.CharField(max_length=100)
    related_images = ListField()
    offering_description = DictField()
    notification_url = models.CharField(max_length=100)
    creation_date = models.DateTimeField()
    publication_date = models.DateTimeField(null=True, blank=True)

    def is_owner(self, user):
        return self.owner_admin_user == user

    class Meta:
        app_label = 'wstore'
        unique_together = ('name', 'owner_organization', 'version')


# The resources are the frontend components of an application
# a resource could be a web based component or an API used to
# access backend components
class Resource(models.Model):
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    provider = models.ForeignKey(User)
    resource_type = models.CharField(max_length=50)
    content_type = models.CharField(max_length=50)
    # Organization
    description = models.TextField()
    state = models.CharField(max_length=50)
    download_link = models.CharField(max_length=200)
    resource_path = models.CharField(max_length=100)
    offerings = ListField(models.ForeignKey(Offering))

    class Meta:
        app_label = 'wstore'
        unique_together = ('name', 'provider', 'version')
