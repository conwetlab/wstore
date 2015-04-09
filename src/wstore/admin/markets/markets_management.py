# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from urllib2 import HTTPError

from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.models import Marketplace
from wstore.market_adaptor.marketadaptor import MarketAdaptor


def get_marketplaces():

    marketplaces = Marketplace.objects.all()
    result = []

    for market in marketplaces:
        result.append({
            'name': market.name,
            'host': market.host,
            'api_version': market.api_version
        })

    return result


def register_on_market(name, host, api_version, site):

    if host[-1] != '/':
        host += '/'

    # Check if the marketplace already exists
    if len(Marketplace.objects.filter(name=name) | Marketplace.objects.filter(host=host)) > 0:
        raise PermissionDenied('Marketplace already registered')

    store_name = settings.STORE_NAME

    marketplace = Marketplace(
        name=name,
        host=host,
        api_version=api_version
    )

    marketadaptor = MarketAdaptor(host)

    store_info = {
        'store_name': store_name,
        'store_uri': site,
    }

    marketadaptor.add_store(store_info)

    try:
        marketplace.save()
    except Exception as e:
        # If the marketplace model creation fails it is necesary to unregister the store
        # in order to avoid an inconsistent state
        marketadaptor.delete_store(store_name)
        raise e


def unregister_from_market(market):

    marketplace = None
    try:
        marketplace = Marketplace.objects.get(name=market)
    except:
        raise Exception('Not found')

    host = marketplace.host
    if host[-1] != '/':
        host += '/'

    marketadaptor = MarketAdaptor(host)

    try:
        marketadaptor.delete_store(settings.STORE_NAME)
    except HTTPError:
        raise Exception('Bad Gateway')

    marketplace.delete()
