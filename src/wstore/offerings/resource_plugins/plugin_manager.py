
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

from wstore.offerings.resource_plugins.plugin_error import PluginError
from wstore.store_commons.utils.version import is_valid_version


class PluginManager():

    _plugins = {}
    _instance = None

    def __init__(self):
        if self._instance is not None:
            raise ValueError('This class has been already instantiated')

    def validate_plugin_info(self, plugin_info):

        valid = True
        reason = None
        # Check plugin_info format
        if not isinstance(plugin_info, dict):
            valid = False
            reason = 'Plugin info must be a dict instance'

        # Validate structure
        if valid and not "name" in plugin_info:
            valid = False
            reason = 'Missing required field: name'

        if valid and not "author" in plugin_info:
            valid = False
            reason = 'Missing required field: author'

        if valid and not 'formats' in plugin_info:
            valid = False
            reason = 'Missing required field: formats'

        if valid and not "media_types" in plugin_info:
            valid = False
            reason = 'Missing required field: media_types'

        if valid and not 'options' in plugin_info:
            valid = False
            reason  = 'Missing required field: options'

        if valid and not 'module' in plugin_info:
            valid = False
            reason = 'Missing required field: module'

        if valid and not 'version' in plugin_info:
            valid = False
            reason = 'Missing required field: version'

        # Validate types
        if valid and not isinstance(plugin_info['name'], str) and not isinstance(plugin_info['name'], unicode):
            valid = False
            reason = 'Plugin name must be an string'

        if valid and not isinstance(plugin_info['author'], str) and not isinstance(plugin_info['author'], unicode):
            valid = False
            reason = 'Plugin author must be an string'

        if valid and not isinstance(plugin_info['formats'], list):
            valid = False
            reason = 'Plugin formats must be a list'

        if valid and not isinstance(plugin_info['media_types'], list):
            valid = False
            reason = 'Plugin media_types must be a list'

        if valid and not isinstance(plugin_info['options'], dict):
            valid = False
            reason = 'Plugin options must be an object'

        if valid and not isinstance(plugin_info['module'], str) and not isinstance(plugin_info['module'], unicode):
            valid = False
            reason = 'Plugin module must be an string'

        if valid and not is_valid_version(plugin_info['version']):
            valid = False
            reason = 'Invalid format in plugin version'

        return (valid, reason)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PluginManager()

        return cls._instance
