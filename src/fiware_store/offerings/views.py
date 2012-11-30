import json
import rdflib
import re
import base64
import os

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings

from store_commons.resource import Resource
from store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from repository_adaptor.repositoryAdaptor import RepositoryAdaptor
from market_adaptor.marketadaptor import MarketAdaptor
from fiware_store.models import Application
from fiware_store.models import Resource as Store_resource
from fiware_store.models import UserProfile
from fiware_store.models import Repository


class ApplicationCollection(Resource):

    # Creates a new offering asociated with the user
    # that is create a new application model
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):

        # Obtains the user profile of the user
        user = request.user
        profile = UserProfile.objects.get(user=user)
        content_type = get_content_type(request)[0]
        data = {}

        # Checks the provider role
        if 'provider' in profile.roles:

            if content_type == 'application/json':
                try:
                    json_data = json.loads(request.raw_post_data)
                    data['name'] = json_data['name']
                    data['version'] = json_data['version']

                    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
                        return build_error_response(request, 400, 'Invalid version format')

                    data['related_images'] = []

                    # Create the directory for app media
                    path = os.path.join(settings.MEDIA_ROOT, data['name'])
                    os.makedirs(path)
                    image = json_data['image']

                    # Save the application image or logo
                    f = open(os.path.join(path, image['name']), "wb")
                    dec = base64.b64decode(image['data'])
                    f.write(dec)

                    data['image_url'] = settings.MEDIA_URL + data['name'] + '/' + image['name']
                    # Save screen shots
                    if 'related_images' in json_data:
                        for image in json_data['related_images']:

                            # images must be encoded in base64 format
                            f = open(os.path.join(path, image['name']), "wb")
                            dec = base64.b64decode(image['data'])
                            f.write(dec)

                            data['related_images'].append(settings.MEDIA_URL + data['name'] + '/' + image['name'])

                    # Save USDL document

                    offering_description = json_data['offering_description']
                    graph = rdflib.Graph()
                    graph.parse(data=offering_description['data'], format=offering_description['content_type'])
                    data['offering_description'] = graph.serialize(format='json-ld')

                    repository = Repository.objects.get(name=json_data['repository'])
                    repository_adaptor = RepositoryAdaptor(repository.host, 'storeApplicationCollection')
                    offering_id = profile.organization + '__' + data['name'] + '__' + data['version']

                    data['description_url'] = repository_adaptor.upload(offering_id, offering_description['content_type'], offering_description['data'])

                except HTTPError, e:
                    return build_error_response(request, 502, 'Bad Gateway')
                except:
                    return build_error_response(request, 400, 'Invalid content')
            else:
                pass  # TODO xml parsed

            Application.objects.create(
                name=data['name'],
                owner_organization=profile.organization,
                owner_admin_user=user,
                version=data['version'],
                state='uploaded',
                description_url=data['description_url'],
                resources=[],
                comments=[],
                tags=[],
                image_url=data['image_url'],
                related_images=data['related_images'],
                offering_description=json.loads(data['offering_description']))
        else:
            pass

        return build_error_response(request, 201, 'Created')


class ApplicationEntry(Resource):

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def update(self, request, offering, organization, version):

        # Obtains the offering
        offering = None
        try:
            offering = Application.objects.get(name=offering, owner_organization=organization, version=version)
        except:
            return build_error_response(request, 404, 'Not found')

        if not offering.is_owner(request.user):
            return build_error_response(request, 401, 'Unauthorized')


class ResourceCollection(Resource):

    # Creates a new resource asociated with an user
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):

        user = request.user
        profile = UserProfile.objects.get(user=user)
        content_type = get_content_type(request)[0]
        resource_data = {}

        if 'provider' in profile.roles:

            if content_type == 'application/json':
                try:
                    data = json.loads(request.raw_post_data)
                    resource_data = {
                        'name': data['name'],
                        'version': data['version'],
                        'resource_type': data['type'],
                        'description': data['description'],
                        'image': data['image'],
                        'related_elements': data['related_elements'],
                        'repository': data['repository'],
                    }
                except:
                    return build_error_response(request, 400, 'Invalid JSON content')
            else:  # TODO parse xml request
                pass

            rep = Repository.objects.get(name=resource_data['repository'])
            host = rep.host

            repository_adaptor = RepositoryAdaptor(host, 'storeResourceCollection')

            elem_dir = []
            # Uploads the different elements of the resource to the repository
            for element in resource_data['related_elements']:
                try:
                    elem_dir.append(repository_adaptor.upload(element.name, element.content_type, element.data))
                except:
                    return build_error_response(request, 502, 'Bad gateway')

            Store_resource.objects.create(
                name=resource_data['name'],
                provider=user,
                version=resource_data['version'],
                resource_type=resource_data['type'],
                description=resource_data['description'],
                # image
                related_elements=elem_dir,
            )
        else:
            pass


class ResourceEntry(Resource):
    pass
