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


RESOURCE_DATA1 = {
    'name': 'Resource1',
    'version': '1.0',
    'description': 'Test resource 1',
    'content_type': 'text/plain',
    'state': 'created',
    'open': False,
    'link': 'http://localhost/media/resources/resource1',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_DATA2 = {
    'name': 'Resource2',
    'version': '2.0',
    'description': 'Test resource 2',
    'content_type': 'text/plain',
    'state': 'created',
    'open': False,
    'link': 'http://localhost/media/resources/resource2',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_DATA3 = {
    'name': 'Resource3',
    'version': '2.0',
    'description': 'Test resource 3',
    'content_type': 'text/plain',
    'state': 'created',
    'open': True,
    'link': 'http://localhost/media/resources/resource3',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_DATA4 = {
    'name': 'Resource4',
    'version': '1.0',
    'description': 'Test resource 4',
    'content_type': 'text/plain',
    'state': 'used',
    'open': True,
    'link': 'http://localhost/media/resources/resource4',
    'resource_type': 'API',
    'metadata': {}
}

RESOURCE_IN_USE_DATA = {
    'description': 'Test resource 4',
}

RESOURCE_CONTENT = {
    'content': {
        'name': 'test_usdl.rdf',
        'data': ''
    },
}

UPDATE_DATA1 = {
    'description': 'Test resource 1',
    'content_type': 'text/plain',
    'open': False
}

UPDATE_DATA2 = {
    'content_type': 'text/plain',
    'open': False
}

UPGRADE_CONTENT = {
    'version': '1.0',
    'content': {
        'name': 'test_usdl.rdf',
        'data': ''
    },
}

UPGRADE_LINK = {
    'version': '1.0',
    'link': 'http://newlinktoresource.com'
}

UPGRADE_INV_LINK = {
    'version': '1.0',
    'link': 'invalid link'
}
