import json
import rdflib
import re
import base64
import os
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from urlparse import urlparse, urljoin

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse

from store_commons.resource import Resource
from store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from repository_adaptor.repositoryAdaptor import RepositoryAdaptor
from market_adaptor.marketadaptor import MarketAdaptor
from fiware_store.models import Offering
from fiware_store.models import Marketplace
from fiware_store.models import Resource as Store_resource
from fiware_store.models import UserProfile
from fiware_store.models import Repository
from store_commons.utils.usdlParser import USDLParser


class OfferingCollection(Resource):

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
                    dir_name = profile.organization + '__' + data['name'] + '__' + data['version']
                    path = os.path.join(settings.MEDIA_ROOT, dir_name)
                    os.makedirs(path)
                    image = json_data['image']

                    # Save the application image or logo
                    f = open(os.path.join(path, image['name']), "wb")
                    dec = base64.b64decode(image['data'])
                    f.write(dec)

                    data['image_url'] = settings.MEDIA_URL + dir_name + '/' + image['name']
                    # Save screen shots
                    if 'related_images' in json_data:
                        for image in json_data['related_images']:

                            # images must be encoded in base64 format
                            f = open(os.path.join(path, image['name']), "wb")
                            dec = base64.b64decode(image['data'])
                            f.write(dec)

                            data['related_images'].append(settings.MEDIA_URL + dir_name + '/' + image['name'])

                    # Save USDL document

                    offering_description = json_data['offering_description']
                    graph = rdflib.Graph()
                    graph.parse(data=offering_description['data'], format=offering_description['content_type'])
                    data['offering_description'] = graph.serialize(format='json-ld')

                    repository = Repository.objects.get(name=json_data['repository'])
                    repository_adaptor = RepositoryAdaptor(repository.host, 'storeOfferingCollection')
                    offering_id = profile.organization + '__' + data['name'] + '__' + data['version']

                    data['description_url'] = repository_adaptor.upload(offering_id, offering_description['content_type'], offering_description['data'])

                except HTTPError, e:
                    return build_error_response(request, 502, 'Bad Gateway')
                except:
                    return build_error_response(request, 400, 'Invalid content')
            else:
                pass  # TODO xml parsed

            Offering.objects.create(
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

    @method_decorator(login_required)
    def read(self, request):
        # TODO support for xml requests
        # Read the query string in order to know the filter and the page
        filter_ = request.GET.get('filter', 'all')

        if filter_ == 'provider':

            # Get all the offerings owned by the provider using raw mongodb access
            connection = MongoClient()
            db = connection.fiwarestore_db
            # Get provider id
            user = User.objects.get(username=request.user)
            offerings = db.fiware_store_application

            if	request.GET.get('state') == 'uploaded':
                prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id), 'state': 'uploaded'})
            elif request.GET.get('state') == 'all':
                prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id)})

            result = []
            # TODO pagination
            for offer in prov_offerings:
                offer['owner_admin_user_id'] = user.username
                offer['_id'] = str(offer['_id'])
                parser = USDLParser(json.dumps(offer['offering_description']), 'application/json')
                offer['offering_description'] = parser.parse()
                resource_content = []

                for resource in offer['resources']:
                    res = Store_resource.objects.get(id=resource)
                    resource_content.append({
                        'name': res.name,
                        'version': res.version,
                        'description': res.description
                    })
                offer['resources'] = resource_content

                # Use to avoid the serialization error with marketplaces id
                if 'marketplaces' in offer:
                    del(offer['marketplaces'])

                result.append(offer)

            mime_type = 'application/JSON; charset=UTF-8'
            return HttpResponse(json.dumps(result), status=200, mimetype=mime_type)


class OfferingEntry(Resource):

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def update(self, request, organization, name, version):
        # Obtains the offering
        offering = None
        content_type = get_content_type(request)[0]
        try:
            offering = Offering.objects.get(name=name, owner_organization=organization, version=version)
        except:
            return build_error_response(request, 404, 'Not found')

        if not offering.is_owner(request.user):
            return build_error_response(request, 401, 'Unauthorized')

        if content_type == 'application/json':

            try:
                data = json.loads(request.raw_post_data)
                # Publish request
                if 'type' in data and data['type'] == 'publish':

                    for market in data['markets']:

                        m = Marketplace.objects.get(name=market)
                        market_adaptor = MarketAdaptor(m.host)
                        info = {
                            'name': offering.name,
                            'url': offering.description_url
                        }
                        market_adaptor.add_service(settings.STORE_NAME, info)
                        offering.marketplaces.append(m.pk)

                    offering.state = 'published'
                    offering.save()

                else:

                    added_resources = []
                    offering_resources = []
                    for of_res in offering.resources:
                        offering_resources.append(of_res)

                    for res in data:
                        resource = Store_resource.objects.get(name=res['name'], version=res['version'], provider=request.user)

                        if not ObjectId(resource.pk) in offering_resources:
                            added_resources.append(resource.pk)
                        else:
                            offering_resources.remove(ObjectId(resource.pk))

                    # added_resources contains the resources to be added to the offering
                    # and offering_resources the resurces to be deleted from the offering

                    for add_res in added_resources:
                        resource = Store_resource.objects.get(pk=add_res)
                        resource.offerings.append(offering.pk)
                        resource.save()
                        offering.resources.append(ObjectId(add_res))

                    for del_res in offering_resources:
                        resource = Store_resource.objects.get(pk=del_res)
                        resource.offerings.remove(offering.pk)
                        resource.save()
                        offering.resources.remove(del_res)

                    offering.save()

            except:
                return build_error_response(request, 400, 'Invalid json content')

        return build_error_response(request, 200, 'Ok')

    @method_decorator(login_required)
    def delete(self, request, organization, name, version):
        # If the offering has been purchased it is not deleted
        # it is marked as deleted in order to allow customers that
        # have puerchased the offering to intall it if needed
        offering = Offering.objects.get(name=name, owner_organization=organization, version=version)
        if request.user != offering.owner_admin_user:
            build_error_response(request, 401, 'Unauthorized')

        if offering.state == 'uploaded':
            #delete the usdl description from the repository
            parsed_url = urlparse(offering.description_url)
            path = parsed_url.path
            host = parsed_url.scheme + '://' + parsed_url.netloc
            path = path.split('/')
            host += '/' + path[1] + '/' + path[2]
            collection = path[3]

            repository_adaptor = RepositoryAdaptor(host, collection)
            repository_adaptor.delete(path[4])

            if offering.related_images or offering.resources:
                # If the offering has media files delete them
                dir_name = organization + '__' + name + '__' + version
                path = os.path.join(settings.MEDIA_ROOT, dir_name)
                files = os.listdir(path)

                for f in files:
                    file_path = os.path.join(path, f)
                    os.remove(file_path)

                os.rmdir(path)

            offering.delete()
        else:
            # Delete the offering from marketplaces
            offering.state = 'deleted'
            offering.save()

        return build_error_response(request, 204, 'No content')

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
                        'type': 'download',
                        'description': data['description'],
                    }
                    if 'content' in data:
                        resource = data['content']

                        #decode the content and save the media file
                        file_name = user.username + '__' + data['name'] + '__' + data['version'] + '__' + resource['name']
                        path = os.path.join(settings.MEDIA_ROOT, 'resources')
                        file_path = os.path.join(path, file_name)
                        f = open(file_path, "wb")
                        dec = base64.b64decode(resource['data'])
                        f.write(dec)
                        resource_data['content_path'] = file_path
                        resource_data['link'] = ''

                    elif 'link' in data:
                        # Add the download link
                        resource_data['link'] = data['link']
                        resource_data['content_path'] = ''

                except:
                    return build_error_response(request, 400, 'Invalid JSON content')
            else:  # TODO parse xml request
                pass

            Store_resource.objects.create(
                name=resource_data['name'],
                provider=user,
                version=resource_data['version'],
                resource_type=resource_data['type'],
                description=resource_data['description'],
                download_link=resource_data['link'],
                resource_path=resource_data['content_path']
            )
        else:
            pass

        return build_error_response(request, 201, 'Created')

    @method_decorator(login_required)
    def read(self, request):
        profile = UserProfile.objects.get(user=request.user)
        response = []
        if 'provider' in profile.roles:

            resouces = Store_resource.objects.filter(provider=request.user)

            for res in resouces:
                response.append({
                    'name': res.name,
                    'version': res.version,
                    'description': res.description
                })

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

class ResourceEntry(Resource):
    pass
