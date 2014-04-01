# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

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

import json

from mock import MagicMock


def decorator_mock(func):
    """
    Generic mock for decorators
    """
    def wrapper(*args, **kargs):
        return func(*args, **kargs)
    return wrapper


def decorator_mock_callable(*fagrs):
    """
    Generic mock for decorators
    """
    def wrap(func):
        def wrapper(*args, **kargs):
            return func(*args, **kargs)
        return wrapper
    return wrap


def build_response_mock(request, code, msg):
    """
    Mock for build_response method
    """
    if code > 199 and code < 300:
        status = 'correct'
    else:
        status = 'error'

    response = MagicMock()
    response.content = json.dumps({
        'result': status,
        'message': msg
    })
    response.status_code = code
    return response


class HTTPResponseMock():

    data = None
    status = None
    mimetype = None

    def __init__(self, data, status=None, mimetype=None):
        self.data = data
        self.status = status
        self.mimetype = mimetype


def mock_request(method, url, data, headers):
    return {
        'method': method,
        'url': url,
        'data': data,
        'headers': headers
    }
