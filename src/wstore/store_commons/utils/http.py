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

import socket
from urlparse import urljoin
from xml.dom.minidom import getDOMImplementation

from django.conf import settings
from django.shortcuts import render
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from wstore.store_commons.utils.error_response import get_json_response, get_xml_response, get_unicode_response
from wstore.store_commons.utils import mimeparser


def get_html_basic_error_response(request, mimetype, status_code, message):
    return render(request, '%s.html' % status_code, {'request_path': request.path}, status=status_code, content_type=mimetype)

FORMATTERS = {
    'application/json; charset=utf-8': get_json_response,
    'application/xml; charset=utf-8': get_xml_response,
    'text/plain; charset=utf-8': get_unicode_response,
}


def build_response(request, status_code, msg, extra_formats=None, headers=None):
    if extra_formats is not None:
        formatters = extra_formats.copy()
        formatters.update(FORMATTERS)
    else:
        formatters = FORMATTERS

    if request.META.get('HTTP_X_REQUESTED_WITH', '') == 'XMLHttpRequest':
        mimetype = 'application/json; charset=utf-8'
    else:
        mimetype = mimeparser.best_match(formatters.keys(), request.META.get('HTTP_ACCEPT', 'text/plain'))

    response = HttpResponse(formatters[mimetype](request, mimetype, status_code, msg), mimetype=mimetype, status=status_code)
    if headers is None:
        headers = {}

    for header_name in headers:
        response[header_name] = headers[header_name]

    return response


def get_content_type(request):
    content_type_header = request.META.get('CONTENT_TYPE')
    if content_type_header is None:
        return '', ''
    else:
        return content_type_header.split(';', 1)

def authentication_required(func):

    def wrapper(self, request, *args, **kwargs):
        if request.user.is_anonymous():

            return build_response(request, 401, 'Authentication required', headers={
                 'WWW-Authenticate': 'Cookie realm="Acme" form-action="%s" cookie-name="%s"' % (settings.LOGIN_URL, settings.SESSION_COOKIE_NAME)
             })

        return func(self, request, *args, **kwargs)

    return wrapper

def supported_request_mime_types(mime_types):

    def wrap(func):
        def wrapper(self, request, *args, **kwargs):
            if get_content_type(request)[0] not in mime_types:
                msg = _("Unsupported request media type")
                return build_response(request, 415, msg)

            return func(self, request, *args, **kwargs)
        return wrapper

    return wrap


def identity_manager_required(func):
    """
    Decorator that specifies a functionality that can only be achieved
    if an identity manager is in use
    """

    def wrapper(self, request, *args, **kwargs):
        if not settings.OILAUTH:
            return build_response(request, 403, 'The requested features are not supported for the current authentication method')
        return func(self, request, *args, **kwargs)
    return wrapper


def get_current_domain(request=None):
    if hasattr(settings, 'FORCE_DOMAIN'):
        return settings.FORCE_DOMAIN
    else:
        try:
            return get_current_site(request).domain
        except:
            return socket.gethostbyaddr(socket.gethostname())[0] + ':' + str(getattr(settings, 'FORCE_PORT', 8000))


def get_current_scheme(request=None):
    if hasattr(settings, 'FORCE_PROTO'):
        return settings.FORCE_PROTO
    elif (request is not None) and request.is_secure():
        return 'https'
    else:
        return 'http'


def get_absolute_reverse_url(viewname, request=None, **kwargs):
    path = reverse(viewname, **kwargs)
    scheme = get_current_scheme(request)
    return urljoin(scheme + '://' + get_current_domain(request) + '/', path)


def get_absolute_static_url(url, request=None):
    scheme = get_current_scheme()
    base = urljoin(scheme + '://' + get_current_domain(request), settings.STATIC_URL)
    return urljoin(base, url)
