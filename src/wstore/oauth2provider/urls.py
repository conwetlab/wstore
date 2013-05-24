# -*- coding: utf-8 -*-


from django.conf.urls.defaults import include, patterns, url


urlpatterns = patterns('wstore.oauth2provider.views',

    url('^oauth2/auth$', 'provide_authorization_code', name='oauth2provider.auth'),
    url('^oauth2/token$', 'provide_authorization_token', name='oauth2provider.token'),

)
