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

from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import wstore.urls
from wstore.views import ServeMedia

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/?$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/?$', 'wstore.store_commons.authentication.logout', name='logout'),
    url(r'^media/(?P<path>.+)/(?P<name>[\w -.]+)/?$', ServeMedia(permitted_methods=('GET',)))
)

urlpatterns += wstore.urls.urlpatterns
