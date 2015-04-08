# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from __future__ import unicode_literals

import requests
from urlparse import urlparse, urljoin

from django.core.exceptions import PermissionDenied


CKAN_ENDPOINT = 'https://data.lab.fi-ware.org'

    
def validate_dataset(user, url):
    valid = True
    reason = None

    parsed_url = urlparse(url)
    ckan_parsed = urlparse(CKAN_ENDPOINT)

    # Check if the url corresponds to a CKAN dataset
    if ckan_parsed.netloc != parsed_url.netloc:
        return (valid, reason)

    try:
        # Extract dataset id
        dataset_id = parsed_url.path.split('/')[2]

        # Get dataset metainfo
        meta_url = urljoin(CKAN_ENDPOINT, 'api/action/dataset_show?id=' + dataset_id)
        meta_info_res = requests.get(meta_url, headers={'X-Auth-token': user.userprofile.access_token})
        
        if meta_info_res.status_code != 200:
            raise PermissionDenied('Invalid resource: The user is not authorized to access the dataset')
        
        meta_info = meta_info_res.json()
        user_id = meta_info['result']['creator_user_id']

        # Get user info
        user_url = urljoin(CKAN_ENDPOINT, 'api/action/user_show?id=' + user_id)
        user_info_res = requests.get(user_url, headers={'X-Auth-token': user.userprofile.access_token})
        
        if user_info_res.status_code != 200:
            raise PermissionDenied('Invalid resource: The user is not authorized to access the dataset')

        user_info = user_info_res.json()

        # Validate owner
        if user_info['result']['name'] != user.username:
            raise PermissionDenied('Invalid resource: The user is not the owner of the dataset')

    except PermissionDenied as e:
        valid = False
        reason = unicode(e)
    except Exception as e:
        # If an error occur the resource is not valid
        valid = False
        reason = 'Invalid resource: The provided URL is not valid'

    return (valid, reason)
