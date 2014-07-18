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

from __future__ import unicode_literals

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

    # Check contents
    if not 'name' in data or not 'version' in data or\
    not 'description' in data or not 'content_type' in data:
        raise ValueError('Invalid request: Missing required field')

    # Check version format
    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise ValueError('Invalid version format')

    # Check name format
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
            raise ValueError('Invalid request: Missing resource content')

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
            'state': res.state,
            'open': res.open,
            'link': res.get_url()
        }

        response.append(resource_info)

    return response


def delete_resource(resource):

    if resource.state == 'deleted':
        raise PermissionDenied('The resource is already deleted')

    # If the resource is not included in any offering delete it
    if not len(resource.offerings):
        # Delete files if needed
        if resource.resource_path:
            path = os.path.join(settings.BASEDIR, resource.resource_path[1:])
            os.remove(path)

        resource.delete()
    else:
        # If the resource is part of an offering mark it as deleted
        resource.state = 'deleted'
        resource.save()


def update_resource(resource, data, file_=None):

    # Check that the resource can be updated
    if resource.state == 'deleted':
        raise PermissionDenied('Deleted resources cannot be updated')

    # If the resource is included in an offering
    # only the resource fields can be updated
    # (not the resource itself)
    if len(resource.offerings):

        invalid_data = False
        for field in data:
            if field != 'content_type' and field != 'description':
                invalid_data = True
                break

        if not invalid_data and file_:
            invalid_data = True

        if invalid_data:
            raise PermissionDenied('The resource is being used, only description and content type can be modified')

    if 'name' in data:
        if not is_valid_id(data['name']):
            raise ValueError('Invalid name format')

        resource.name = data['name']

    if 'version' in data:
        if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
            raise ValueError('Invalid version format')

        invalid_version = False
        prev_versions = Resource.objects.filter(name=resource.name, provider=resource.provider)
        for vers in prev_versions:
            if vers != resource and is_lower_version(data['version'], vers.version):
                invalid_version = True
                break

        if invalid_version:
            raise ValueError('A bigger version of the resource exists')

        resource.version = data['version']

    if 'content_type' in data:
        if not isinstance(data['content_type'], unicode) and not isinstance(data['content_type'], str):
            raise TypeError('Invalid type for content_type field')

        resource.content_type = data['content_type']

    if 'open' in data:
        if not isinstance(data['open'], bool):
            raise TypeError('Invalid type for open field')

        resource.open = data['open']

    if 'description' in data:
        if not isinstance(data['description'], unicode) and not isinstance(data['description'], str):
            raise TypeError('Invalid type for description field')

        resource.description = data['description']

    if file_ or 'content' in data:
        # Check if a file exists
        if not resource.resource_path == '':
            # Remove file
            path = os.path.join(settings.BASEDIR, resource.resource_path[1:])
            os.remove(path)
            resource.resource_path = ''

        if file_:
            file_content = file_
        else:
            file_content = data['content']

        # Create new file
        resource.resource_path = _save_resource_file(resource.provider.name, resource.name, resource.version, file_content)
        resource.download_link = ''
    elif 'link' in data:
        if not is_valid_url(data['link']):
            raise ValueError('Invalid URL format')

        if not resource.resource_path == '':
            # Remove file
            path = os.path.join(settings.BASEDIR, resource.resource_path[1:])
            os.remove(path)
            resource.resource_path = ''

        resource.download_link = data['link']

    resource.save()
