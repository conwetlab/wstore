# -*- coding: utf-8 -*-


from django.contrib import admin
from wstore.oauth2provider import models


admin.site.register(models.Application)
admin.site.register(models.Code)
admin.site.register(models.Token)
