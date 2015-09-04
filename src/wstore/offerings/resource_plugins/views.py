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

import json

from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import authentication_required
from wstore.models import ResourcePlugin


class PluginCollection(Resource):

    @authentication_required
    def read(self, request):
        """
        This view is used to retrieve the existing resource plugin types
        """
        # Load basic types
        result = [{
            'name': 'Downloadable',
            'plugin_id': 'downloadable',
            'author': 'Wstore',
            'version': '1',
            'media_types': [],
            'formats': ['FILE', 'URL'],
            'overrides': []
        }, {
            'name': 'API',
            'plugin_id': 'api',
            'author': 'Wstore',
            'version': '1',
            'media_types': [],
            'formats': ['URL'],
            'overrides': []
        }]

        # Get resource plugins
        plugins = ResourcePlugin.objects.all()

        for plugin in plugins:
            plugin_info = {
                'name': plugin.name,
                'plugin_id': plugin.plugin_id,
                'author': plugin.author,
                'version': plugin.version,
                'media_types': plugin.media_types,
                'formats': plugin.formats,
                'overrides': plugin.overrides
            }
            if plugin.form:
                plugin_info['form'] = plugin.form

            result.append(plugin_info)

        mime_type = 'application/JSON; charset=UTF-8'
        return HttpResponse(json.dumps(result), status=200, mimetype=mime_type)
