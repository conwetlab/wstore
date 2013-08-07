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
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from djangotoolbox.fields import ListField
from djangotoolbox.fields import DictField

from wstore.admin.markets.models import *
from wstore.admin.repositories.models import *
from wstore.admin.rss.models import *


class Context(models.Model):

    site = models.OneToOneField(Site)
    top_rated = ListField()
    newest = ListField()
    user_refs = DictField()


class Organization(models.Model):

    name = models.CharField(max_length=50, unique=True)
    notification_url = models.CharField(max_length=300)
    offerings_purchased = ListField()
    payment_info = DictField()
    tax_address = DictField()
    actor_id = models.IntegerField(unique=True, null=True, blank=True)


from wstore.offerings.models import Offering
from wstore.offerings.models import Resource
from wstore.contracting.models import Purchase


class UserProfile(models.Model):

    user = models.OneToOneField(User)
    organization = models.ForeignKey(Organization, blank=True, null=True)  # an user could belong to more than one organization FIXME
    roles = ListField()
    offerings_purchased = ListField()
    offerings_provided = ListField()
    rated_offerings = ListField()
    tax_address = DictField()
    complete_name = models.CharField(max_length=100)
    payment_info = DictField(),
    actor_id = models.IntegerField(unique=True, null=True, blank=True)
    access_token = models.CharField(max_length=150, null=True, blank=True)


def create_user_profile(sender, instance, created, **kwargs):

    if created:
        default_organization = Organization.objects.get_or_create(name='default')
        profile, created = UserProfile.objects.get_or_create(user=instance, roles=['customer'], organization=default_organization[0])


def create_context(sender, instance, created, **kwargs):

    if created:
        Context.objects.get_or_create(site=instance)


#Creates a new user profile when an user is created
post_save.connect(create_user_profile, sender=User)


# Creates a context when the site is created
post_save.connect(create_context, sender=Site)
