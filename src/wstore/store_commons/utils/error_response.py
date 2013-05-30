
from xml.dom.minidom import getDOMImplementation
from django.utils import simplejson

def get_xml_error(request, mimetype, status_code, value):
    dom = getDOMImplementation()

    doc = dom.createDocument(None, "error", None)
    rootelement = doc.documentElement
    text = doc.createTextNode(value)
    rootelement.appendChild(text)
    errormsg = doc.toxml("utf-8")
    doc.unlink()

    return errormsg



def get_json_error_response(request, mimetype, status_code, message):
    return simplejson.dumps({
        'result': 'error',
        'message': message
    })
