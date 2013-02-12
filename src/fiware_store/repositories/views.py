import json
from lxml import etree
from urllib2 import HTTPError

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from store_commons.resource import Resource
from store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from fiware_store.models import Repository


class RepositoryCollection(Resource):

    # Register a new repository on the store
    # in order to be able to upload and
    # download resources
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):

        if not request.user.is_staff:  # Only an admin could register a new repository
            return build_error_response(request, 401, 'Unautorized')

        content_type = get_content_type(request)[0]

        name = None
        host = None
        # Content types json and xml are supported
        if content_type == 'application/json':

            try:
                content = json.loads(request.raw_post_data)
                name = content['name']
                host = content['host']
            except:
                msg = "Request body is not valid JSON data"
                return build_error_response(request, 400, msg)

        else:

            try:
                content = etree.fromstring(request.raw_post_data)
                name = content.xpath('/marketplace/name')[0].text
                host = content.xpath('/marketplace/host')[0].text
            except:
                msg = "Request body is not valid XML data"
                return build_error_response(request, 400, msg)

        # Check if the repository name is in use
        existing = True

        try:
            Repository.objects.get(name=name)
        except:
            existing = False

        if existing:
            return build_error_response(request, 400, 'The repository name is in use')

        Repository.objects.create(name=name, host=host)

        return build_error_response(request, 201, 'Created')  # TODO use a generic method

    @method_decorator(login_required)
    def read(self, request):

        # Read Accept header to know the response mime type, JSON by default
        accept = request.META.get('ACCEPT', '')
        repositories = Repository.objects.all()
        response = None
        mime_type = None

        if accept == '' or accept.find('application/JSON') > -1:
            response = []

            for rep in repositories:
                response.append({
                    'name': rep.name,
                    'host': rep.host
                })

            response = json.dumps(response)
            mime_type = 'application/JSON; charset=UTF-8'

        elif accept.find('application/xml') > -1:
            root_elem = etree.Element('Repositories')

            for rep in repositories:
                rep_elem = etree.SubElement(root_elem, 'Repository')
                name_elem = etree.SubElement(rep_elem, 'Name')
                name_elem.text = rep.name
                host_elem = etree.SubElement(rep_elem, 'Host')
                host_elem.text = rep.host

            response = etree.tounicode(root_elem)
            mime_type = 'application/xml; charset=UTF-8'

        else:
            return build_error_response(request, 400, 'Invalid requested type')

        return HttpResponse(response, status=200, mimetype=mime_type)


class RepositoryEntry(Resource):

    @method_decorator(login_required)
    def delete(self, request, repository):

        if not request.user.is_staff:
            return build_error_response(request, 401, 'Unathorized')

        rep = None
        try:
            rep = Repository.objects.get(name=repository)
        except:
            return build_error_response(request, 404, 'Not found')

        rep.delete()
        return build_error_response(request, 204, 'No content')
