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
from django.utils.translation import ugettext as _


class Application(models.Model):

    client_id = models.CharField(_('Client ID'), max_length=40, blank=False, primary_key=True)
    client_secret = models.CharField(_('Client secret'), max_length=40, blank=False)
    redirect_uri = models.CharField(_('Redirect URI'), max_length=255, blank=True)
    name = models.CharField(_('Application Name'), max_length=40, blank=False)
    home_url = models.CharField(_('URL'), max_length=255, blank=False)

    def __unicode__(self):
        return unicode(self.name)


class Code(models.Model):

    client = models.ForeignKey(Application)
    user = models.ForeignKey(User)
    scope = models.CharField(_('Scope'), max_length=255, blank=True)
    code = models.CharField(_('Code'), max_length=255, blank=False)
    expires_in = models.CharField(_('Expires in'), max_length=40, blank=True)

    class Meta:
        unique_together = ('client', 'code')

    def __unicode__(self):
        return unicode(self.code)


class Token(models.Model):

    token = models.CharField(_('Token'), max_length=40, blank=False, primary_key=True)

    client = models.ForeignKey(Application)
    user = models.ForeignKey(User)

    scope = models.CharField(_('Scope'), max_length=255, blank=True)
    token_type = models.CharField(_('Token type'), max_length=10, blank=False)
    refresh_token = models.CharField(_('Refresh token'), max_length=40, blank=True)
    expires_in = models.CharField(_('Expires in'), max_length=40, blank=True)
