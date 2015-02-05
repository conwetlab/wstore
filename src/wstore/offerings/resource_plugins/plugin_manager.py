
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

class PluginManager():

    _plugins = {}
    _instance = None

    def __init__(self):
        if self._instance is not None:
            raise ValueError('This class has been already instantiated')

    def register_plugin(self, plugin_info):

        # Check plugin_info format
        if not isinstance(plugin_info, dict):
            raise TypeError('Plugin info must be a dict instance')

        if not 'type' in plugin_info:
            raise ValueError('Missing required field: type')

        if not 'options' in plugin_info:
            raise ValueError('Missing required field: options')

        # Validate plugin type field
        if not isinstance(plugin_info['type'], str) and not isinstance(plugin_info['type'], unicode):
            raise TypeError('Plugin type must be an string')

        
    def subscribe_on_create(self):
        pass

    def subscribe_on_update(self):
        pass

    def subscribe_on_upgrade(self):
        pass

    def subscribe_on_delete(self):
        pass

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PluginManager()

        return cls._instance
