# -*- coding: utf-8 -*-

# Copyright (c) 2013-2015 CoNWeT Lab., Universidad Politécnica de Madrid

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
from bson import ObjectId

from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.models import Resource, Offering, ResourcePlugin
from wstore.offerings.models import ResourceVersion
from wstore.store_commons.utils.name import is_valid_id, is_valid_file
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.version import is_lower_version
from wstore.store_commons.errors import ConflictError
from wstore.offerings.resource_plugins.plugins.ckan_validation import validate_dataset


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
        Resource.objects.get(name=data['name'], provider=current_organization)
    except:
        existing = False

    if existing:
        raise ConflictError('The resource ' + data['name'] + ' already exists. Please upgrade the resource if you want to provide new content')

    # Check contents
    if not 'name' in data or not 'version' in data or\
    not 'description' in data or not 'content_type' in data or\
    not 'resource_type' in data:
        raise ValueError('Invalid request: Missing required field')

    # Check version format
    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise ValueError('Invalid version format')

    # Check name format
    if not is_valid_id(data['name']):
        raise ValueError('Invalid name format')

    # Validate resource type
    if data['resource_type'] != 'Downloadable' and data['resource_type'] != 'API':
        res_type_model = ResourcePlugin.objects.filter(name=data['resource_type'])

        if not len(res_type_model) > 0:
            raise ValueError('Invalid resource type')

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

            validation = validate_dataset(provider, data['link'])

            if not validation[0]:
                raise PermissionDenied(validation[1])

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
        open=data.get('open', False),
        resource_type=data['resource_type'],
        meta_info=data.get('meta', {})
    )


def upgrade_resource(resource, data, file_=None):

    # Validate data
    if not 'version' in data:
        raise ValueError('Missing a required field: Version')

    # Check version format
    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise ValueError('Invalid version format')

    if not is_lower_version(resource.version, data['version']):
        raise ValueError('The new version cannot be lower that the current version: ' + data['version'] + ' - ' + resource.version)

    # Check resource state
    if resource.state == 'deleted':
        raise PermissionDenied('Deleted resources cannot be upgraded')

    # Save the old version
    resource.old_versions.append(ResourceVersion(
        version=resource.version,
        resource_path=resource.resource_path,
        download_link=resource.download_link
    ))

    # Update new version number
    resource.version = data['version']

    # Update offerings
    if file_ or 'content' in data:
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

        resource.download_link = data['link']
        resource.resource_path = ''
    else:
        raise ValueError('No resource has been provided')

    resource.save()


def get_provider_resources(provider, filter_=None, pagination=None):

    if pagination and (not 'start' in pagination or not 'limit' in pagination):
        raise ValueError('Missing required parameter in pagination')

    if pagination and (not int(pagination['start']) > 0 or not int(pagination['limit']) > 0):
        raise ValueError('Invalid pagination limits')

    response = []

    if pagination:
        x = int(pagination['start']) -1
        y = x+int(pagination['limit'])
        resources = Resource.objects.filter(provider=provider.userprofile.current_organization)[x:y]
    else:
        resources = Resource.objects.filter(provider=provider.userprofile.current_organization)

    for res in resources:
        # Filter by open property if needed
        if (filter_ == 'true' and not res.open) or (filter_ == 'false' and res.open):
            continue

        state = res.state
        if state != 'deleted' and len(res.offerings):
            state = 'used'

        resource_info = {
            'name': res.name,
            'version': res.version,
            'description': res.description,
            'content_type': res.content_type,
            'state': state,
            'open': res.open,
            'link': res.get_url(),
            'resource_type': res.resource_type
        }
        response.append(resource_info)
    return response


def _remove_resource(resource):
    # Delete files if needed
    if resource.resource_path:
        path = os.path.join(settings.BASEDIR, resource.resource_path[1:])
        os.remove(path)

    resource.delete()


def delete_resource(resource):

    if resource.state == 'deleted':
        raise PermissionDenied('The resource is already deleted')

    # If the resource is not included in any offering delete it
    if not len(resource.offerings):
        _remove_resource(resource)
    else:
        # If the resource is part of an offering check if all the
        # offerings are in uploaded state
        used_offerings = []
        for off in resource.offerings:
            offering = Offering.objects.get(pk=off)

            # Remove resource from uploaded offerings
            if offering.state == 'uploaded':
                offering.resources.remove(ObjectId(resource.pk))
                offering.save()
            else:
                used_offerings.append(off)

        # If the resource is not included in any offering delete it
        if not len(used_offerings):
            _remove_resource(resource)
        else:
            resource.offerings = used_offerings
            resource.state = 'deleted'
            resource.save()


def update_resource(resource, data):

    # Check that the resource can be updated
    if resource.state == 'deleted':
        raise PermissionDenied('Deleted resources cannot be updated')

    # If the resource is included in an offering
    # only the resource fields can be updated
    # (not the resource itself)
    if len(resource.offerings):

        invalid_data = False
        for field in data:
            if field != 'description':
                invalid_data = True
                break

        if invalid_data:
            raise PermissionDenied('The resource is being used, only description can be modified')

    # Check that no contents has been provided
    if 'content' in data or 'link' in data:
        raise ValueError('Resource contents cannot be updated. Please upgrade the resource to provide new contents')

    if 'name' in data:
        raise ValueError('Name field cannot be updated since is used to identify the resource')

    if 'version' in data:
        raise ValueError('Version field cannot be updated since is used to identify the resource')

    # Update fields
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

    resource.save()
