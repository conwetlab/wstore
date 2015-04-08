
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

from wstore.store_commons.utils.version import is_valid_version
from wstore.store_commons.utils.name import is_valid_id


class PluginManager():

    def _validate_plugin_form(self, form_info):
        """
        Validates the structure of the form definition of a plugin
        included in the package.json file
        """
        reason = None
        valid_types = ['text', 'textarea', 'checkbox', 'select']

        for k, v in form_info.iteritems():
            # Validate component
            if not isinstance(v, dict):
                reason = 'Invalid form field: ' + k + ' entry is not an object'
                break

            # Validate type value
            if 'type' not in v:
                reason = 'Invalid form field: Missing type in ' + k + ' entry'
                break

            if not v['type'] in valid_types:
                reason = 'Invalid form field: type ' + v['type'] + ' in ' + k + ' entry is not a valid type'
                break

            # Validate name format
            if not is_valid_id(k):
                reason = 'Invalid form field: ' + k + ' is not a valid name'
                break

            # Validate specific fields
            if v['type'] == 'checkbox' and 'default' in v and not isinstance(v['default'], bool):
                reason = 'Invalid form field: default field in ' + k + ' entry must be a boolean'
                break

        return reason

    def validate_plugin_info(self, plugin_info):
        """
        Validates the structure of the package.json file of a plugin
        """

        reason = None
        # Check plugin_info format
        if not isinstance(plugin_info, dict):
            reason = 'Plugin info must be a dict instance'

        # Validate structure
        if reason is None and "name" not in plugin_info:
            reason = 'Missing required field: name'

        # Validate types
        if reason is None and not isinstance(plugin_info['name'], str) and not isinstance(plugin_info['name'], unicode):
            reason = 'Plugin name must be an string'

        if reason is None and not is_valid_id(plugin_info['name']):
            reason = 'Invalid name format: invalid character'

        if reason is None and "author" not in plugin_info:
            reason = 'Missing required field: author'

        if reason is None and 'formats' not in plugin_info:
            reason = 'Missing required field: formats'

        if reason is None and 'module' not in plugin_info:
            reason = 'Missing required field: module'

        if reason is None and 'version' not in plugin_info:
            reason = 'Missing required field: version'

        if reason is None and not isinstance(plugin_info['author'], str) and not isinstance(plugin_info['author'], unicode):
            reason = 'Plugin author must be an string'

        if reason is None and not isinstance(plugin_info['formats'], list):
            reason = 'Plugin formats must be a list'

        # Validate formats
        if reason is None:
            valid_formats = ['FILE', 'URL']
            valid_format = True
            i = 0

            while valid_format and i < len(plugin_info['formats']):
                if not plugin_info['formats'][i] in valid_formats:
                    valid_format = False
                i += 1

            if not valid_format or (i < 1 and i > 2):
                reason = 'Format must contain at least one format of: FILE, URL'

        if reason is None and 'media_types' in plugin_info and not isinstance(plugin_info['media_types'], list):
            reason = 'Plugin media_types must be a list'

        if reason is None and not isinstance(plugin_info['module'], str) and not isinstance(plugin_info['module'], unicode):
            reason = 'Plugin module must be an string'

        if reason is None and not is_valid_version(plugin_info['version']):
            reason = 'Invalid format in plugin version'

        if reason is None and 'form' in plugin_info:
            if not isinstance(plugin_info['form'], dict):
                reason = 'Invalid format in form field, must be an object'
            else:
                reason = self._validate_plugin_form(plugin_info['form'])

        return reason
