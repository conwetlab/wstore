import json
import rdflib
import re
import base64
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from urlparse import urlparse

from django.conf import settings
from django.contrib.auth.models import User

from fiware_store.repository_adaptor.repositoryAdaptor import RepositoryAdaptor
from fiware_store.market_adaptor.marketadaptor import MarketAdaptor
from fiware_store.search.search_engine import SearchEngine
from fiware_store.models import Resource
from fiware_store.models import Repository
from fiware_store.models import Offering
from fiware_store.models import Marketplace
from fiware_store.models import Purchase
from fiware_store.models import UserProfile
from fiware_store.store_commons.utils.usdlParser import USDLParser


def _get_purchased_offerings(user, db, pagination=None):

    # Get the user profile purchased offerings
    user_profile = db.fiware_store_userprofile.find_one({'user_id': ObjectId(user.pk)})
    # Get the user organization purchased offerings
    organization = db.fiware_store_organization.find_one({'_id': user_profile['organization_id']})
    result = []

    # Load user and organization purchased offerings
    user_purchased = user_profile['offerings_purchased']

    # Remove user offerings from organization offerings
    for offer in organization['offerings_purchased']:
        if not offer in user_purchased:
            user_purchased.append(offer)

    # If pagination has been defined take the offerings corresponding to the page
    if pagination:
        skip = int(pagination['skip']) - 1
        limit = int(pagination['limit'])

        if skip < len(user_purchased):
            user_purchased = user_purchased[skip:(skip + limit)]

    # Load user offerings  to the result
    for offer in user_purchased:
        offer_info = db.fiware_store_offering.find_one({'_id': ObjectId(offer)})
        offer_info['state'] = 'purchased'
        offering = Offering.objects.get(pk=offer)
        try:
            purchase = Purchase.objects.get(offering=offering, customer=user)
        except:
            purchase = Purchase.objects.get(offering=offering, owner_organization=organization['name'])
        offer_info['bill'] = purchase.bill
        result.append(offer_info)

    return result


# Gets a set of offerings depending on filter value
def get_offerings(user, filter_='published', owned=False, pagination=None):

    if pagination and (not int(pagination['skip']) > 0 or not int(pagination['limit']) > 0):
        raise Exception('Invalid pagination limits')

    # Get all the offerings owned by the provider using raw mongodb access
    connection = MongoClient()
    db = connection[settings.DATABASES['default']['NAME']]
    offerings = db.fiware_store_offering
    # Pagination: define the first element and the number of elements
    if owned:
        if  filter_ == 'uploaded':
            prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id), 'state': 'uploaded'})
        elif filter_ == 'all':
            prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id)})
        elif  filter_ == 'published':
            prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id), 'state': 'published'})
        elif filter_ == 'purchased':
            if pagination:
                prov_offerings = _get_purchased_offerings(user, db, pagination)
                pagination = None
            else:
                prov_offerings = _get_purchased_offerings(user, db)

    else:
        if  filter_ == 'published':
            prov_offerings = offerings.find({'state': 'published'})

    result = []

    if pagination:
        prov_offerings = prov_offerings.skip(int(pagination['skip']) - 1).limit(int(pagination['limit']))

    profile = UserProfile.objects.get(user=user)
    org = profile.organization

    for offer in prov_offerings:
        offer['owner_admin_user_id'] = User.objects.get(pk=offer['owner_admin_user_id']).username
        offer['_id'] = str(offer['_id'])
        parser = USDLParser(json.dumps(offer['offering_description']), 'application/json')
        offer['offering_description'] = parser.parse()
        resource_content = []

        purchase = None
        # If filter is published change state and add bill to the purchased offerings
        if (not owned and filter_ == 'published') or filter_ == 'purchased':
            found = False

            if str(offer['_id']) in profile.offerings_purchased:
                offering = Offering.objects.get(pk=str(offer['_id']))
                purchase = Purchase.objects.get(offering=offering, customer=user)
                found = True

            elif str(offer['_id']) in org.offerings_purchased:
                offering = Offering.objects.get(pk=str(offer['_id']))
                purchase = Purchase.objects.get(offering=offering, owner_organization=org.name)
                found = True

            if found and filter_ == 'published':
                offer['bill'] = purchase.bill
                offer['state'] = 'purchased'

        # If the offering has been purchased and contains pricing components based on
        # subscriptions the parsed pricing model is replace with the pricing model of the
        # contract
        if purchase != None and ('subscription' in purchase.contract.pricing_model):
            pricing_model = purchase.contract.pricing_model
            offer['offering_description']['pricing']['price_plans'][0]['price_components'] = []

            # Cast renovation date to string in order to avoid serialization problems

            for subs in pricing_model['subscription']:
                subs['renovation_date'] = str(subs['renovation_date'])
                offer['offering_description']['pricing']['price_plans'][0]['price_components'].append(subs)

            if 'single_payment' in pricing_model:
                offer['offering_description']['pricing']['price_plans'][0]['price_components'].extend(pricing_model['single_payment'])

            if 'pay_per_use' in pricing_model:
                offer['offering_description']['pricing']['price_plans'][0]['price_components'].extend(pricing_model['pay_per_use'])

        for resource in offer['resources']:
            res = Resource.objects.get(id=resource)
            res_info = {
                'name': res.name,
                'version': res.version,
                'description': res.description
            }

            if offer['state'] == 'purchased':
                if res.resource_type == 'download':
                    if res.resource_path != '':
                        res_info['link'] = res.resource_path
                    elif res.download_link != '':
                        res_info['link'] = res.download_link

            resource_content.append(res_info)
        offer['resources'] = resource_content

        # Use to avoid the serialization error with marketplaces id
        if 'marketplaces' in offer:
            del(offer['marketplaces'])

        result.append(offer)

    return result


def count_offerings(user, filter_='published', owned=False):

    if owned:
        if  filter_ == 'uploaded':
            count = Offering.objects.filter(owner_admin_user=user, state='uploaded').count()
        elif filter_ == 'all':
            count = Offering.objects.filter(owner_admin_user=user).count()
        elif  filter_ == 'published':
            count = Offering.objects.filter(owner_admin_user=user, state='published').count()
        elif filter_ == 'purchased':
            user_profile = UserProfile.objects.get(user=user)
            count = len(user_profile.offerings_purchased)
            count += len(user_profile.organization.offerings_purchased)

    else:
        if  filter_ == 'published':
            count = Offering.objects.filter(state='published').count()

    return {'number': count}


def get_offering_info(offering, user):

    user_profile = UserProfile.objects.get(user=user)

    # Check if the user has purchased the offering
    state = offering.state

    if offering.pk in user_profile.offerings_purchased:
        state = 'purchased'
        purchase = Purchase.objects.get(offering=offering, customer=user)
    elif offering.pk in user_profile.organization.offerings_purchased:
        state = 'purchased'
        purchase = Purchase.objects.get(offering=offering, owner_organization=user_profile.organization.name)

    # Load offering data
    result = {
        'name': offering.name,
        'owner_organization': offering.owner_organization,
        'owner_admin_user_id': offering.owner_admin_user.username,
        'version': offering.version,
        'state': state,
        'description_url': offering.description_url,
        'rating': offering.rating,
        'comments': offering.comments,
        'tags': offering.tags,
        'image_url': offering.image_url,
        'related_images': offering.related_images,
        'resources': []
    }

    # Load resources
    for res in offering.resources:
        resource = Resource.objects.get(pk=res)
        res_info = {
            'name': resource.name,
            'version': resource.version,
            'description': resource.description
        }

        if state == 'purchased' and resource.resource_type == 'download':
            if resource.resource_path != '':
                res_info['link'] = resource.resource_path
            elif resource.download_link != '':
                res_info['link'] = resource.download_link

        result['resources'].append(res_info)

    # Load offering description
    parser = USDLParser(json.dumps(offering.offering_description), 'application/json')
    result['offering_description'] = parser.parse()

    if state == 'purchased':
        result['bill'] = purchase.bill

        # If the offering has been purchased the parsed pricing model is replaced
        # With the pricing model of the contract in order to included the extra info
        # needed such as renovation dates etc.

        pricing_model = purchase.contract.pricing_model

        if 'subscription' in pricing_model:
            result['offering_description']['pricing']['price_plans'][0]['price_components'] = []
            # Cast renovation date to string in order to avoid serialization problems

            for subs in pricing_model['subscription']:
                subs['renovation_date'] = str(subs['renovation_date'])
                result['offering_description']['pricing']['price_plans'][0]['price_components'].append(subs)

            if 'single_payment' in pricing_model:
                result['offering_description']['pricing']['price_plans'][0]['price_components'].extend(pricing_model['single_payment'])

            if 'pay_per_use' in pricing_model:
                result['offering_description']['pricing']['price_plans'][0]['price_components'].extend(pricing_model['pay_per_use'])

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

    # Get organization
    organization = profile.organization

    # Check if the offering already exists
    existing = True

    try:
        Offering.objects.get(name=data['name'], owner_organization=organization.name, version=data['version'])
    except:
        existing = False

    if existing:
        raise Exception('The offering already exists')

    # Create the directory for app media
    dir_name = organization.name + '__' + data['name'] + '__' + data['version']
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
    rdf_format = offering_description['content_type']

    if rdf_format == 'text/turtle' or rdf_format == 'text/plain':
        rdf_format = 'n3'
    elif rdf_format == 'application/json':
        rdf_format = 'json-ld'

    graph.parse(data=offering_description['data'], format=rdf_format)
    data['offering_description'] = graph.serialize(format='json-ld')

    repository = Repository.objects.get(name=json_data['repository'])
    repository_adaptor = RepositoryAdaptor(repository.host, 'storeOfferingCollection')
    offering_id = organization.name + '__' + data['name'] + '__' + data['version']

    data['description_url'] = repository_adaptor.upload(offering_id, offering_description['content_type'], offering_description['data'])

    offering = Offering.objects.create(
        name=data['name'],
        owner_organization=organization.name,
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

    # Load offering document to the search index
    index_path = os.path.join(settings.BASEDIR, 'fiware_store')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    search_engine = SearchEngine(index_path)
    search_engine.create_index(offering)


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
