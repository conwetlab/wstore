from django.conf.urls import patterns, url


urlpatterns = patterns(
    'wstore.registration.views',
    url(r'^signup/$', 'signup_view',
        name='signup'),
    url(r'^activate/(?P<activation_key>\w+)/$', 'activate_view',
        name='activate'),
)
