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
    notification_url = models.CharField(max_length=300, null=True, blank=True)
    offerings_purchased = ListField()
    private = models.BooleanField(default=True)
    payment_info = DictField()
    tax_address = DictField()
    managers = ListField()
    actor_id = models.IntegerField(null=True, blank=True)


from wstore.offerings.models import Offering
from wstore.offerings.models import Resource
from wstore.contracting.models import Purchase


class UserProfile(models.Model):

    user = models.OneToOneField(User)
    organizations = ListField()
    current_organization = models.ForeignKey(Organization)
    offerings_purchased = ListField()
    offerings_provided = ListField()
    rated_offerings = ListField()
    tax_address = DictField()
    complete_name = models.CharField(max_length=100)
    payment_info = DictField()
    actor_id = models.IntegerField(null=True, blank=True)
    access_token = models.CharField(max_length=150, null=True, blank=True)
    refresh_token = models.CharField(max_length=150, null=True, blank=True)

    def get_current_roles(self):
        roles = []
        for o in self.organizations:
            if o['organization'] == self.current_organization.pk:
                roles = o['roles']
                break

        return roles

    def get_user_roles(self):
        from django.conf import settings
        roles = []

        for o in self.organizations:
            org = Organization.objects.get(pk=o['organization'])

            if settings.OILAUTH:
                # Check actor_id
                if org.actor_id == self.actor_id:
                    roles = o['roles']
                    break
            else:
                # Check organization name
                if org.name == self.user.username:
                    roles = o['roles']
                    break
        return roles

    def is_user_org(self):

        result = False
        # Use the actor_id for identify the user organization
        # in order to avoid problems with nickname changes
        if self.actor_id and self.current_organization.actor_id:
            if self.actor_id == self.current_organization.actor_id:
                result = True
        else:
            if self.user.username == self.current_organization.name:
                result = True

        return result


def create_user_profile(sender, instance, created, **kwargs):

    if created:
        # Create a private organization for the user
        default_organization = Organization.objects.get_or_create(name=instance.username)
        default_organization[0].managers.append(instance.pk)
        default_organization[0].save()

        profile, created = UserProfile.objects.get_or_create(
            user=instance,
            organizations=[{
                'organization': default_organization[0].pk,
                'roles': ['customer']
            }],
            current_organization=default_organization[0]
        )


def create_context(sender, instance, created, **kwargs):

    if created:
        Context.objects.get_or_create(site=instance)


#Creates a new user profile when an user is created
post_save.connect(create_user_profile, sender=User)

# Creates a context when the site is created
post_save.connect(create_context, sender=Site)
