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

from xml.dom.minidom import getDOMImplementation
from django.utils import simplejson

def get_xml_response(request, mimetype, status_code, value):
    dom = getDOMImplementation()

    if status_code >= 400:
        doc = dom.createDocument(None, "error", None)
    else:
        doc = dom.createDocument(None, "message", None)

    rootelement = doc.documentElement
    text = doc.createTextNode(value)
    rootelement.appendChild(text)
    errormsg = doc.toxml("utf-8")
    doc.unlink()

    return errormsg


def get_json_response(request, mimetype, status_code, message):
    response = {
        'message': message
    }
    if status_code >= 400:
        response['result'] = 'error'
    else:
        response['result'] = 'correct'

    return simplejson.dumps(response)
