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


def register_resource(provider, data, file_=None):

    # Check if the resource already exists
    existing = True
    try:
        Resource.objects.get(name=data['name'], provider=provider, version=data['version'])
    except:
        existing = False

    if existing:
        raise Exception('The resource already exists')

    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise Exception('Invalid version format')

    resource_data = {
        'name': data['name'],
        'version': data['version'],
        'description': data['description'],
        'content_type': data['content_type']
    }

    if file_ is None:
        if 'content' in data:
            resource = data['content']

            #decode the content and save the media file
            file_name = provider.username + '__' + data['name'] + '__' + data['version'] + '__' + resource['name']
            path = os.path.join(settings.MEDIA_ROOT, 'resources')
            file_path = os.path.join(path, file_name)
            f = open(file_path, "wb")
            dec = base64.b64decode(resource['data'])
            f.write(dec)
            f.close()
            resource_data['content_path'] = settings.MEDIA_URL + 'resources/' + file_name
            resource_data['link'] = ''

        elif 'link' in data:
            # Add the download link
            resource_data['link'] = data['link']
            resource_data['content_path'] = ''

    else:
        #decode the content and save the media file
        file_name = provider.username + '__' + data['name'] + '__' + data['version'] + '__' + file_.name
        path = os.path.join(settings.MEDIA_ROOT, 'resources')
        file_path = os.path.join(path, file_name)
        f = open(file_path, "wb")
        f.write(file_.read())
        f.close()
        resource_data['content_path'] = settings.MEDIA_URL + 'resources/' + file_name
        resource_data['link'] = ''

    Resource.objects.create(
        name=resource_data['name'],
        provider=provider,
        version=resource_data['version'],
        description=resource_data['description'],
        download_link=resource_data['link'],
        resource_path=resource_data['content_path'],
        content_type=resource_data['content_type']
    )


def get_provider_resources(provider):
    resouces = Resource.objects.filter(provider=provider)
    response = []
    for res in resouces:
        resource_info = {
            'name': res.name,
            'version': res.version,
            'description': res.description,
            'content_type': res.content_type
        }

        response.append(resource_info)

    return response
