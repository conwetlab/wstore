import json
from lxml import etree

from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types,\
authentication_required
from wstore.admin.repositories.repositories_management import register_repository, unregister_repository, get_repositories


class RepositoryCollection(Resource):

    # Register a new repository on the store
    # in order to be able to upload and
    # download resources
    @authentication_required
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

        try:
            register_repository(name, host)
        except Exception, e:
            return build_error_response(request, 400, e.message)

        return build_error_response(request, 201, 'Created')  # TODO use a generic method

    @authentication_required
    def read(self, request):

        # Read Accept header to know the response mime type, JSON by default
        accept = request.META.get('ACCEPT', '')
        response = None
        mime_type = None
        repositories = get_repositories()

        if accept == '' or accept.find('application/JSON') > -1:
            response = json.dumps(repositories)
            mime_type = 'application/JSON; charset=UTF-8'

        elif accept.find('application/xml') > -1:
            root_elem = etree.Element('Repositories')

            for rep in repositories:
                rep_elem = etree.SubElement(root_elem, 'Repository')
                name_elem = etree.SubElement(rep_elem, 'Name')
                name_elem.text = rep['name']
                host_elem = etree.SubElement(rep_elem, 'Host')
                host_elem.text = rep['host']

            response = etree.tounicode(root_elem)
            mime_type = 'application/xml; charset=UTF-8'

        else:
            return build_error_response(request, 400, 'Invalid requested type')

        return HttpResponse(response, status=200, mimetype=mime_type)


class RepositoryEntry(Resource):

    @authentication_required
    def delete(self, request, repository):

        if not request.user.is_staff:
            return build_error_response(request, 401, 'Unathorized')

        try:
            unregister_repository(repository)
        except Exception, e:
            if e.message == 'Not found':
                code = 404
            else:
                code = 400

            return build_error_response(request, code, e.message)

        return build_error_response(request, 204, 'No content')
