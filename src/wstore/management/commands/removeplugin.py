
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

from django.core.management.base import BaseCommand, CommandError

from wstore.offerings.resource_plugins.plugin_loader import PluginLoader


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        Loads a new resource plugin
        """

        # Check arguments
        if len(args) != 1:
            raise CommandError("Error: Please specify the plugin to be deleted")

        try:
            name = args[0]
            # Load plugin
            plugin_loader = PluginLoader()
            plugin_loader.uninstall_plugin(name)
        except Exception as e:
            raise CommandError(unicode(e))

        self.stdout.write("The plugin has been removed\n")
