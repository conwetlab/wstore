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


class Plugin():

    def on_pre_create_validation(self, provider, data, file_=None):
        return data

    def on_post_create_validation(self, provider, data, file_=None):
        pass

    def on_pre_create(self, provider, data):
        pass

    def on_post_create(self, resource):
        pass

    def on_pre_update(self, resource):
        pass

    def on_post_update(self, resource):
        pass

    def on_pre_upgrade_validation(self, resource, data, file_=None):
        return data

    def on_post_upgrade_validation(self, resource, data, file_=None):
        pass

    def on_pre_upgrade(self, resource):
        pass

    def on_post_upgrade(self, resource):
        pass

    def on_pre_delete(self, resource):
        pass

    def on_post_delete(self, resource):
        pass
