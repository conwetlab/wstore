from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import wstore.urls
from wstore.views import ServeMedia

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^usdleditor', 'usdl-editor.views.usdl_editor', name='usdl_editor'),
    url(r'^login/?$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/?$', 'wstore.store_commons.authentication.logout', name='logout'),
    url(r'^media/(?P<path>.+)/(?P<name>[\w -.]+)/?$', ServeMedia(permitted_methods=('GET',)))
)

urlpatterns += wstore.urls.urlpatterns
