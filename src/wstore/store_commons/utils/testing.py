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
import os
import shutil
from mock import MagicMock

from django.conf import settings


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


def _save_ixdir(orig_info, dest_info):
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, orig_info['module'])
    index_path = os.path.join(index_path, orig_info['name'])

    destination_path = os.path.join(settings.BASEDIR, 'wstore')
    destination_path = os.path.join(destination_path, dest_info['module'])
    destination_path = os.path.join(destination_path, dest_info['name'])

    shutil.move(index_path, destination_path)


def _restore_ixdir(orig_info, dest_info):
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, orig_info['module'])
    index_path = os.path.join(index_path, orig_info['name'])

    try:
        shutil.rmtree(index_path)
    except:
        pass

    destination_path = os.path.join(settings.BASEDIR, 'wstore')
    destination_path = os.path.join(destination_path, dest_info['module'])
    destination_path = os.path.join(destination_path, dest_info['name'])

    shutil.move(destination_path, index_path)


def save_indexes():
    orig_info = {
        'module': 'search',
        'name': 'indexes'
    }
    dest_info = {
        'module': 'test',
        'name': 'indexes'
    }
    _save_ixdir(orig_info, dest_info)


def restore_indexes():
    orig_info = {
        'module': 'search',
        'name': 'indexes'
    }
    dest_info = {
        'module': 'test',
        'name': 'indexes'
    }
    _restore_ixdir(orig_info, dest_info)


def save_tags():
    orig_info = {
        'module': 'social',
        'name': 'indexes'
    }
    dest_info = {
        'module': 'test',
        'name': 'tag_indexes'
    }
    _save_ixdir(orig_info, dest_info)


def restore_tags():
    orig_info = {
        'module': 'social',
        'name': 'indexes'
    }
    dest_info = {
        'module': 'test',
        'name': 'tag_indexes'
    }
    _restore_ixdir(orig_info, dest_info)
