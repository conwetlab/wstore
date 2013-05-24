# -*- coding: utf-8 -*-


from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _


class Application(models.Model):

    client_id = models.CharField(_('Client ID'), max_length=40, blank=False, primary_key=True)
    client_secret = models.CharField(_('Client secret'), max_length=40, blank=False)
    redirect_uri = models.CharField(_('Redirect URI'), max_length=255, blank=True)

class Code(models.Model):

    client = models.ForeignKey(Application)
    user = models.ForeignKey(User)
    scope = models.CharField(_('Scope'), max_length=255, blank=True)
    code = models.CharField(_('Code'), max_length=255, blank=False)


class Token(models.Model):

    token = models.CharField(_('Token'), max_length=40, blank=False, primary_key=True)

    client = models.ForeignKey(Application)
    user = models.ForeignKey(User)

    scope = models.CharField(_('Scope'), max_length=255, blank=True)
    token_type = models.CharField(_('Token type'), max_length=10, blank=False)
    refresh_token = models.CharField(_('Refresh token'), max_length=40, blank=True)
    expires_in = models.CharField(_('Expires in'), max_length=40, blank=True)
