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

from django.conf.urls.defaults import patterns, url, include

import wstore.oauth2provider.urls
from wstore import views
from wstore.admin import views as admin_views
from wstore.admin.markets import views as market_views
from wstore.admin.repositories import views as rep_views
from wstore.admin.rss import views as rss_views
from wstore.admin.users import views as user_views
from wstore.admin.organizations import views as org_views
from wstore.offerings import views as offering_views
from wstore.contracting import views as contracting_views
from wstore.search import views as search_views
from wstore.charging_engine import views as charging_views
from wstore.social.tagging import views as tagging_views
from wstore.repository_adaptor import usdl_proxy
from wstore.offerings.resource_plugins import views as plugins_views

urlpatterns = patterns('',

    # Views
    url(r'^/?$', 'wstore.views.home', name='home'),
    url(r'^search/?$', 'wstore.views.home_search', name='home_search'),
    url(r'^search/keyword/(?P<keyword>[\w -]+)/?$', 'wstore.views.home_search_text', name='home_search_text'),
    url(r'^search/tag/(?P<tag>[\w -]+)/?$', 'wstore.views.home_search_tag', name='home_search_tag'),
    url(r'^search/resource/(?P<org>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/?$', 'wstore.views.home_search_resource', name='home_search_resource'),
    url(r'^offering/(?P<org>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/?$', 'wstore.views.home_details', name='home_details'),
    url(r'^administration/?$', 'wstore.views.admin', name='admin'),
    url(r'^catalogue/?$', 'wstore.views.catalogue', name='catalogue'),
    url(r'^organization/$', 'wstore.views.organization', name='organization'),

    # API
    url(r'^api/administration/search$', admin_views.ResourceSearch(permitted_methods=('GET',)), name='resource_search'),
    url(r'^api/administration/marketplaces/?$', market_views.MarketplaceCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/repositories/?$', rep_views.RepositoryCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/repositories/(?P<repository>[\w -]+)/default?$', rep_views.RepositoryDefaultEntry(permitted_methods=('POST', ))),
    url(r'^api/administration/rss/?$', rss_views.RSSCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/rss/(?P<rss>[\w -]+)/?$', rss_views.RSSEntry(permitted_methods=('GET', 'DELETE', 'PUT'))),
    url(r'^api/administration/profiles/?$', user_views.UserProfileCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/organizations/?$', org_views.OrganizationCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/units/?$', admin_views.UnitCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/currency/?$', admin_views.CurrencyCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/administration/currency/(?P<currency>[\w -]+)/?$', admin_views.CurrencyEntry(permitted_methods=('DELETE', 'PUT'))),
    url(r'^api/administration/marketplaces/(?P<market>[\w -]+)/?$', market_views.MarketplaceEntry(permitted_methods=('DELETE',))),
    url(r'^api/administration/repositories/(?P<repository>[\w -]+)/?$', rep_views.RepositoryEntry(permitted_methods=('DELETE',))),
    url(r'^api/administration/profiles/(?P<username>[\w -]+)/?$', user_views.UserProfileEntry(permitted_methods=('GET', 'PUT'))),
    url(r'^api/administration/organizations/change', 'wstore.admin.organizations.views.change_current_organization', name='change_current_organization'),
    url(r'^api/administration/organizations/(?P<org>[\w -]+)/?$', org_views.OrganizationEntry(permitted_methods=('PUT', 'GET'))),
    url(r'^api/administration/organizations/(?P<org>[\w -]+)/users/?$', org_views.OrganizationUserCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/offering/offerings/?$', offering_views.OfferingCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/offering/offerings/latest/?$', offering_views.NewestCollection(permitted_methods=('GET',))),
    url(r'^api/offering/offerings/toprated/?$', offering_views.TopRatedCollection(permitted_methods=('GET',))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/?$', offering_views.OfferingEntry(permitted_methods=('GET', 'PUT', 'DELETE'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/publish/?$', offering_views.PublishEntry(permitted_methods=('POST',))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/bind/?$', offering_views.BindEntry(permitted_methods=('POST',))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/review/?$', offering_views.ReviewCollection(permitted_methods=('POST', 'GET'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/review/(?P<review>\w+)/?$', offering_views.ReviewEntry(permitted_methods=('PUT', 'DELETE'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/review/(?P<review>\w+)/reply/?$', offering_views.ResponseEntry(permitted_methods=('PUT', 'DELETE'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/tag/?$', tagging_views.TagCollection(permitted_methods=('GET', 'PUT'))),
    url(r'^api/offering/offerings/(?P<organization>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/usdl/?$', usdl_proxy.USDLCollection(permitted_methods=('GET',))),
    url(r'^api/offering/resources/(?P<provider>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/?$', offering_views.ResourceEntry(permitted_methods=('DELETE', 'POST', 'PUT'))),
    url(r'^api/offering/resources/?$', offering_views.ResourceCollection(permitted_methods=('GET', 'POST'))),
    url(r'^api/offering/resources/plugins?$', plugins_views.PluginCollection(permitted_methods=('GET', ))),
    url(r'^api/offering/applications/?$', offering_views.ApplicationCollection(permitted_methods=('GET',))),
    url(r'^api/contracting/?$', contracting_views.PurchaseCollection(permitted_methods=('POST',))),
    url(r'^api/contracting/form/?$', contracting_views.PurchaseFormCollection(permitted_methods=('POST', 'GET'))),
    url(r'^api/contracting/(?P<reference>[\w]+)/?$', contracting_views.PurchaseEntry(permitted_methods=('GET', 'PUT'))),
    url(r'^api/contracting/(?P<reference>[\w]+)/accept/?$', charging_views.PayPalConfirmation(permitted_methods=('GET',))),
    url(r'^api/contracting/(?P<reference>[\w]+)/cancel/?$', charging_views.PayPalCancelation(permitted_methods=('GET',))),
    url(r'^api/contracting/(?P<reference>[\w]+)/accounting/?$', charging_views.ServiceRecordCollection(permitted_methods=('POST', 'GET'))),
    url(r'^api/search/keyword/(?P<text>[\w -]+)/?$', search_views.SearchEntry(permitted_methods=('GET',))),
    url(r'^api/search/tag/(?P<tag>[\w -]+)/?$', tagging_views.SearchTagEntry(permitted_methods=('GET',))),
    url(r'^api/search/resource/(?P<org>[\w -]+)/(?P<name>[\w -]+)/(?P<version>[\d.]+)/?$', search_views.SearchByResourceEntry(permitted_methods=('GET',))),
    url(r'^api/provider/?$', views.ProviderRequest(permitted_methods=('POST',))),
    url(r'', include('social_auth.urls')),
)

urlpatterns += wstore.oauth2provider.urls.urlpatterns
