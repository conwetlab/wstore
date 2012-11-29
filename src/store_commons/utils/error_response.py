
from xml.dom.minidom import getDOMImplementation
from django.utils import simplejson

def get_xml_error(value):
    dom = getDOMImplementation()

    doc = dom.createDocument(None, "error", None)
    rootelement = doc.documentElement
    text = doc.createTextNode(value)
    rootelement.appendChild(text)
    errormsg = doc.toxml("utf-8")
    doc.unlink()

    return errormsg


def get_json_error_response(value):
    response = {}

    response['result'] = "error"
    response["message"] = value

    response = simplejson.dumps(response)

    return response
