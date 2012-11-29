from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import fiware_store.urls

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^usdleditor', 'usdl-editor.views.usdl_editor', name='usdl_editor'),
    url(r'^login/?$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/?$', 'store_commons.authentication.logout', name='logout'),
)

urlpatterns += fiware_store.urls.urlpatterns
