from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import fiware_store.urls

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^usdleditor', 'usdl-editor.views.usdl_editor', name='usdl_editor'),
    url(r'^login/?$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/?$', 'fiware_store.store_commons.authentication.logout', name='logout'),
    url(r'^media/(?P<path>.+)/(?P<name>[\w -.]+)/?$', 'fiware_store.views.serve_media' ,name='serve_media')
)

urlpatterns += fiware_store.urls.urlpatterns
