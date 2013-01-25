import json
import rdflib
import re
import base64
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from urlparse import urlparse

from django.conf import settings

from repository_adaptor.repositoryAdaptor import RepositoryAdaptor
from market_adaptor.marketadaptor import MarketAdaptor
from fiware_store.models import Resource
from fiware_store.models import Repository
from fiware_store.models import Offering
from fiware_store.models import Marketplace
from store_commons.utils.usdlParser import USDLParser


# Gets all the offerings from an user provider  
def get_provider_offerings(provider, filter_='all'):
     # Get all the offerings owned by the provider using raw mongodb access
    connection = MongoClient()
    db = connection[settings.DATABASES['default']['NAME']]
    offerings = db.fiware_store_offering

    if  filter_ == 'uploaded':
        prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(provider.id), 'state': 'uploaded'})
    elif filter_ == 'all':
        prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(provider.id)})

    result = []
    # TODO pagination
    for offer in prov_offerings:
        offer['owner_admin_user_id'] = provider.username
        offer['_id'] = str(offer['_id'])
        parser = USDLParser(json.dumps(offer['offering_description']), 'application/json')
        offer['offering_description'] = parser.parse()
        resource_content = []

        for resource in offer['resources']:
            res = Resource.objects.get(id=resource)
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

    return result

# Creates a new offering including the media files and 
# the repository uploads
def create_offering(provider, profile, json_data):

    data = {}
    data['name'] = json_data['name']
    data['version'] = json_data['version']

    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise Exception('Invalid version format') 

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

    Offering.objects.create(
        name=data['name'],
        owner_organization=profile.organization,
        owner_admin_user=provider,
        version=data['version'],
        state='uploaded',
        description_url=data['description_url'],
        resources=[],
        comments=[],
        tags=[],
        image_url=data['image_url'],
        related_images=data['related_images'],
        offering_description=json.loads(data['offering_description'])
    )

def publish_offering(offering, data):

    for market in data['marketplaces']:

        if not len(offering.resources) > 0:
            raise Exception('It is not possible to publish an offering without resources')

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

def delete_offering(offering):
    # If the offering has been purchased it is not deleted
    # it is marked as deleted in order to allow customers that
    # have purchased the offering to intall it if needed

    #delete the usdl description from the repository
    parsed_url = urlparse(offering.description_url)
    path = parsed_url.path
    host = parsed_url.scheme + '://' + parsed_url.netloc
    path = path.split('/')
    host += '/' + path[1] + '/' + path[2]
    collection = path[3]

    repository_adaptor = RepositoryAdaptor(host, collection)
    repository_adaptor.delete(path[4])

    if offering.state == 'uploaded':

        if offering.related_images or offering.resources:
            # If the offering has media files delete them
            dir_name = offering.owner_organization + '__' + offering.name + '__' + offering.version
            path = os.path.join(settings.MEDIA_ROOT, dir_name)
            files = os.listdir(path)

            for f in files:
                file_path = os.path.join(path, f)
                os.remove(file_path)

            os.rmdir(path)

        offering.delete()
    else:
        # Delete the offering from marketplaces
        for market in offering.marketplaces:

            m = Marketplace.objects.get(pk=market)
            market_adaptor = MarketAdaptor(m.host)
            market_adaptor.delete_service(settings.STORE_NAME, offering.name)

        offering.state = 'deleted'
        offering.save()

def bind_resources(offering, data, provider):

    added_resources = []
    offering_resources = []
    for of_res in offering.resources:
        offering_resources.append(of_res)

    for res in data:
        resource = Resource.objects.get(name=res['name'], version=res['version'], provider=provider)

        if not ObjectId(resource.pk) in offering_resources:
            added_resources.append(resource.pk)
        else:
            offering_resources.remove(ObjectId(resource.pk))

    # added_resources contains the resources to be added to the offering
    # and offering_resources the resurces to be deleted from the offering

    for add_res in added_resources:
        resource = Resource.objects.get(pk=add_res)
        resource.offerings.append(offering.pk)
        resource.save()
        offering.resources.append(ObjectId(add_res))

    for del_res in offering_resources:
        resource = Resource.objects.get(pk=del_res)
        resource.offerings.remove(offering.pk)
        resource.save()
        offering.resources.remove(del_res)

    offering.save()
