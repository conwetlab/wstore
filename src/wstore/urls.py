
from django.conf.urls.defaults import patterns, include, url

from wstore import views
from wstore.markets import views as market_views
from wstore.repositories import views as rep_views
from wstore.offerings import views as offering_views
from wstore.contracting import views as contracting_views
from wstore.search import views as search_views
from wstore.charging_engine import views as charging_views

urlpatterns = patterns('',

    # Views
    url(r'^/?$', 'wstore.views.home', name='home'),
    url(r'^administration/?$', 'wstore.views.admin', name='admin'),
    url(r'^catalogue/?$', 'wstore.views.catalogue', name='catalogue'),

    # API
    url(r'^api/administration/marketplaces/?$', market_views.MarketplaceCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/repositories/?$', rep_views.RepositoryCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/marketplaces/(?P<market>[\w -]+)/?$', market_views.MarketplaceEntry(permitted_methods=('GET', 'PUT', 'DELETE'))),
    url(r'^api/administration/repositories/(?P<repository>[\w -]+)/?$', rep_views.RepositoryEntry(permitted_methods=('GET', 'PUT', 'DELETE'))),
    url(r'^api/offering/offerings/?$', offering_views.OfferingCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/?$', offering_views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/publish?$', offering_views.PublishEntry(permitted_methods=('POST',))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/bind?$', offering_views.BindEntry(permitted_methods=('POST',))),
    url(r'^api/offering/resources/?$', offering_views.ResourceCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/contracting/?$', contracting_views.PurchaseCollection(permitted_methods=('POST',))),
    url(r'^api/contracting/(?P<reference>[\w]+)/?$', contracting_views.PurchaseEntry(permitted_methods=('GET', 'PUT'))),
    url(r'^api/contracting/(?P<reference>[\w]+)/accept?$', charging_views.PayPalConfirmation(permitted_methods=('GET',))),
    url(r'^api/contracting/(?P<reference>[\w]+)/cancel?$', charging_views.PayPalCancelation(permitted_methods=('GET',))),
    url(r'^api/search/(?P<text>[\w -]+)/?$', search_views.SearchEntry(permitted_methods=('GET',))),
)
