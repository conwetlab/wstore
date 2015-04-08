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

import os
import json
import zipfile
from shutil import rmtree

from django.conf import settings
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

from wstore.offerings.resource_plugins.plugin_manager import PluginManager
from wstore.offerings.resource_plugins.plugin_error import PluginError
from wstore.offerings.resource_plugins.plugin_rollback import installPluginRollback
from wstore.models import ResourcePlugin, Resource
from wstore.offerings.resource_plugins.plugin import Plugin


class PluginLoader():

    _plugin_manager = None
    _plugins_path = None
    _plugins_module = None

    def __init__(self):
        self._plugin_manager = PluginManager()
        self._plugins_path = os.path.join(settings.BASEDIR, 'wstore')
        self._plugins_path = os.path.join(self._plugins_path, 'offerings')
        self._plugins_path = os.path.join(self._plugins_path, 'resource_plugins')
        self._plugins_path = os.path.join(self._plugins_path, 'plugins')
        self._plugins_module = 'wstore.offerings.resource_plugins.plugins.'

    @installPluginRollback
    def install_plugin(self, path, logger=None):

        # Validate package file
        if not zipfile.is_zipfile(path):
            raise PluginError('Invalid package format: Not a zip file')

        # Uncompress plugin file
        with zipfile.ZipFile(path, 'r') as z:

            # Validate that the file package.json exists
            if 'package.json' not in z.namelist():
                raise PluginError('Missing package.json file')

            # Read package metainfo
            json_file = z.read('package.json')
            try:
                json_info = json.loads(json_file)
            except:
                raise PluginError('Invalid format in package.json file. JSON cannot be parsed')

            # Create a directory for the plugin
            # Validate plugin info
            validation = self._plugin_manager.validate_plugin_info(json_info)

            # Create plugin id
            plugin_id = json_info['name'].lower().replace(' ', '-')
            if len(ResourcePlugin.objects.filter(plugin_id=plugin_id)) > 0:
                raise PluginError('A plugin with the same id (' + plugin_id + ') already exists')

            if validation is not None:
                raise PluginError('Invalid format in package.json file. ' + validation)

            # Check if the directory already exists
            plugin_path = os.path.join(self._plugins_path, plugin_id)

            # Create the directory
            os.mkdir(plugin_path)

            if logger is not None:
                logger.log_action('PATH', plugin_path)

            # Extract files
            z.extractall(plugin_path)

            # Create a  __init__.py file if needed
            open(os.path.join(plugin_path, '__init__.py'), 'a').close()

        # Validate plugin main class
        module = self._plugins_module + plugin_id + '.' + json_info['module']
        module_class_name = module.split('.')[-1]
        module_package = module.partition('.' + module_class_name)[0]

        module_class = getattr(__import__(module_package, globals(), locals(), [module_class_name], -1), module_class_name)

        if Plugin not in module_class.__bases__:
            raise PluginError('No Plugin implementation has been found')

        # Save plugin model
        ResourcePlugin.objects.create(
            plugin_id=plugin_id,
            name=json_info['name'],
            version=json_info['version'],
            author=json_info['author'],
            module=module,
            formats=json_info['formats'],
            media_types=json_info.get('media_types', []),
            form=json_info.get('form', {})
        )

        return plugin_id

    def uninstall_plugin(self, plugin_id):
        """
        Removes a plugin from the system including model and files
        """

        # Get plugin model
        try:
            plugin_model = ResourcePlugin.objects.get(plugin_id=plugin_id)
        except:
            raise ObjectDoesNotExist('The plugin ' + plugin_id + ' is not registered')

        name = plugin_model.name
        # Check if the plugin is in use
        resources = Resource.objects.filter(resource_type=name)

        if len(resources) > 0:
            raise PermissionDenied('The plugin ' + plugin_id + ' is being used in some resources')

        # Remove plugin files
        plugin_path = os.path.join(self._plugins_path, plugin_id)

        rmtree(plugin_path)

        # Remove model
        plugin_model.delete()
