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

import base64
import os
import re

from django.conf import settings

from wstore.models import Resource
from wstore.store_commons.utils.name import is_valid_id, is_valid_file
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.version import is_lower_version
from django.core.exceptions import PermissionDenied


def _save_resource_file(provider, name, version, file_):
    # Load file contents
    if isinstance(file_, dict):
        f_name = file_['name']
        content = base64.b64decode(file_['data'])
    else:
        f_name = file_.name
        content = file_.read()

    # Check file name
    if not is_valid_file(f_name):
        raise ValueError('Invalid file name format: Unsupported character')

    # Create file
    file_name = provider + '__' + name + '__' + version + '__' + f_name
    path = os.path.join(settings.MEDIA_ROOT, 'resources')
    file_path = os.path.join(path, file_name)
    f = open(file_path, "wb")
    f.write(content)
    f.close()

    return settings.MEDIA_URL + 'resources/' + file_name


def register_resource(provider, data, file_=None):

    # Check if the resource already exists
    existing = True
    current_organization = provider.userprofile.current_organization
    try:
        Resource.objects.get(name=data['name'], provider=current_organization, version=data['version'])
    except:
        existing = False

    if existing:
        raise ValueError('The resource already exists')

    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise ValueError('Invalid version format')

    if not is_valid_id(data['name']):
        raise ValueError('Invalid name format')

    # Check if a bigger version of the resource exists
    res_versions = Resource.objects.filter(name=data['name'], provider=current_organization)

    invalid_version = False
    for prev_ver in res_versions:
        if is_lower_version(data['version'], prev_ver.version):
            invalid_version = True
            break

    if invalid_version:
        raise ValueError('A bigger version of the resource exists')

    resource_data = {
        'name': data['name'],
        'version': data['version'],
        'description': data['description'],
        'content_type': data['content_type']
    }

    if not file_:
        if 'content' in data:
            resource_data['content_path'] = _save_resource_file(current_organization.name, data['name'], data['version'], data['content'])
            resource_data['link'] = ''

        elif 'link' in data:
            # Add the download link
            # Check link format
            if not is_valid_url(data['link']):
                raise ValueError('Invalid resource link format')

            resource_data['link'] = data['link']
            resource_data['content_path'] = ''

    else:
        resource_data['content_path'] = _save_resource_file(current_organization.name, data['name'], data['version'], file_)
        resource_data['link'] = ''

    Resource.objects.create(
        name=resource_data['name'],
        provider=current_organization,
        version=resource_data['version'],
        description=resource_data['description'],
        download_link=resource_data['link'],
        resource_path=resource_data['content_path'],
        content_type=resource_data['content_type'],
        state='created',
        open=data.get('open', False)
    )


def get_provider_resources(provider, filter_=None):
    resources = Resource.objects.filter(provider=provider.userprofile.current_organization)
    response = []
    for res in resources:
        # Filter by open property if needed
        if (filter_ == 'true' and not res.open) or (filter_ == 'false' and res.open):
            continue
        
        resource_info = {
            'name': res.name,
            'version': res.version,
            'description': res.description,
            'content_type': res.content_type,
            'open': res.open
        }

        response.append(resource_info)

    return response

def delete_resource(resource):

    # If the resource is not included in any offering delete it
    if len(resource.offerings) == 0:
        resource.delete()
    else:
        # If the resource is part of an offering mark it as deleted
        resource.state = 'deleted'
        resource.save()

