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

from wstore.models import ResourcePlugin, Resource
from functools import wraps


def load_plugin_module(module):
    module_class_name = module.split('.')[-1]
    module_package = module.partition('.' + module_class_name)[0]

    module_class = getattr(__import__(module_package, globals(), locals(), [module_class_name], -1), module_class_name)

    return module_class()


def _get_plugin_model(name):
    try:
        plugin_model = ResourcePlugin.objects.get(name=name)
    except:
        # Validate resource type
        raise ValueError('Invalid request: The specified resource type is not registered')

    return plugin_model


def register_resource_validation_events(func):

    @wraps(func)
    def wrapper(provider, data, file_=None):
        if 'resource_type' not in data:
            raise ValueError('Invalid request: Missing required field resource_type')

        new_data = data
        if data['resource_type'] != 'Downloadable' and data['resource_type'] != 'API':
            plugin_model = _get_plugin_model(data['resource_type'])
            plugin_module = load_plugin_module(plugin_model.module)

            new_data = plugin_module.on_pre_create_validation(provider, data, file_=file_)

        resource_data = func(provider, new_data, file_=None)

        if data['resource_type'] != 'Downloadable' and data['resource_type'] != 'API':
            plugin_module.on_post_create_validation(provider, data, file_=file)

        return resource_data

    return wrapper


def register_resource_events(func):

    @wraps(func)
    def wrapper(provider, user, data):
        # Get plugin models
        if data['resource_type'] != 'Downloadable' and data['resource_type'] != 'API':

            plugin_model = _get_plugin_model(data['resource_type'])

            # Validate format
            if data['link'] != "" and 'URL' not in plugin_model.formats:
                raise ValueError('Invalid plugin format: URL not allowed for the resource type')

            if data['content_path'] != "" and 'FILE' not in plugin_model.formats:
                raise ValueError('Invalid plugin format: File not allowed for the resource type')

            # Validate mime types
            if len(plugin_model.media_types) > 0 and data['content_type'] not in plugin_model.media_types:
                raise ValueError('Invalid media type: ' + data['content_type'] + ' is not allowed for the resource type')

            # Load plugin module
            plugin_module = load_plugin_module(plugin_model.module)

            # Call on pre create event handler
            plugin_module.on_pre_create(provider, data)

        if data['resource_type'] == 'API' and data['content_path'] != "":
            raise ValueError('Invalid plugin format: File not allowed for the resource type')

        # Call method
        func(provider, user, data)

        # Call on post create event handler
        if data['resource_type'] != 'Downloadable' and data['resource_type'] != 'API':
            resource = Resource.objects.get(name=data['name'], provider=provider, version=data['version'])
            plugin_module.on_post_create(resource)

    return wrapper


def upgrade_resource_validation_events(func):

    @wraps(func)
    def wrapper(resource, data, file_=None):
        new_data = data
        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_model = _get_plugin_model(resource.resource_type)
            plugin_module = load_plugin_module(plugin_model.module)

            new_data = plugin_module.on_pre_upgrade_validation(resource, data, file_=file_)

        resource_data = func(resource, new_data, file_=None)

        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_module.on_post_upgrade_validation(resource, data, file_=file)

        return resource_data

    return wrapper


def upgrade_resource_events(func):

    @wraps(func)
    def wrapper(resource, user):

        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_model = _get_plugin_model(resource.resource_type)

            # Validate format
            if resource.download_link != "" and 'URL' not in plugin_model.formats:
                raise ValueError('Invalid plugin format: URL not allowed for the resource type')

            if resource.resource_path != "" and 'FILE' not in plugin_model.formats:
                raise ValueError('Invalid plugin format: File not allowed for the resource type')

            # Load plugin module
            plugin_module = load_plugin_module(plugin_model.module)

            # Call on pre upgrade event handler
            plugin_module.on_pre_upgrade(resource)

        if resource.resource_type == 'API' and resource.resource_path != "":
            raise ValueError('Invalid plugin format: File not allowed for the resource type')

        # Call method
        func(resource, user)

        # Call on post upgrade event handler
        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_module.on_post_upgrade(resource)

    return wrapper


def update_resource_events(func):

    @wraps(func)
    def wrapper(resource, user):

        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_model = _get_plugin_model(resource.resource_type)

            # Validate media type
            if len(plugin_model.media_types) > 0 and resource.content_type not in plugin_model.media_types:
                raise ValueError('Invalid media type: ' + resource.content_type + ' is not allowed for the resource type')

            # Load plugin module
            plugin_module = load_plugin_module(plugin_model.module)

            # Call on pre update event handler
            plugin_module.on_pre_update(resource)

        # Call method
        func(resource, user)

        # Call on post update event handler
        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_module.on_post_update(resource)

    return wrapper


def delete_resource_events(func):

    @wraps(func)
    def wrapper(resource, user):
        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_model = _get_plugin_model(resource.resource_type)

            # Load plugin module
            plugin_module = load_plugin_module(plugin_model.module)

            # Call on pre delete event handler
            plugin_module.on_pre_delete(resource)

        # Call method
        func(resource, user)

        # Call on post delete event handler
        if resource.resource_type != 'Downloadable' and resource.resource_type != 'API':
            plugin_module.on_post_delete(resource)

    return wrapper
