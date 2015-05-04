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

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if settings.FIWARE_IDM_API_VERSION == 1:
    from wstore.keyrock_backends.keyrock_backend_v1 import FIWARE_AUTHORIZATION_URL, \
        FIWARE_ACCESS_TOKEN_URL, FiwareBackend, fill_internal_user_info

elif settings.FIWARE_IDM_API_VERSION == 2:
    from wstore.keyrock_backends.keyrock_backend_v2 import FIWARE_AUTHORIZATION_URL, \
        FIWARE_ACCESS_TOKEN_URL, FiwareBackend, fill_internal_user_info

else:
    raise ImproperlyConfigured('The provided version for the Idm endpoint is not valid')
