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

import json
import rdflib
import re
import base64
import os
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from urlparse import urlparse

from django.conf import settings

from wstore.repository_adaptor.repositoryAdaptor import RepositoryAdaptor
from wstore.market_adaptor.marketadaptor import MarketAdaptor
from wstore.search.search_engine import SearchEngine
from wstore.offerings.offering_rollback import OfferingRollback
from wstore.models import Resource
from wstore.models import Repository
from wstore.models import Offering
from wstore.models import Marketplace
from wstore.models import Purchase
from wstore.models import UserProfile, Context
from wstore.store_commons.utils.usdlParser import USDLParser


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

    if state == 'purchased':
        if offering.pk in user_profile.rated_offerings:
            state = 'rated'

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
        'creation_date': str(offering.creation_date),
        'publication_date': str(offering.publication_date),
        'resources': []
    }

    # Load resources
    for res in offering.resources:
        resource = Resource.objects.get(pk=res)
        res_info = {
            'name': resource.name,
            'version': resource.version,
            'description': resource.description,
            'content_type': resource.content_type
        }

        if resource.resource_type == 'download':
            res_info['type'] = 'Downloadable resource'
        else:
            res_info['type'] = 'Backend resource'

        if (state == 'purchased' or state == 'rated') and resource.resource_type == 'download':
            if resource.resource_path != '':
                res_info['link'] = resource.resource_path
            elif resource.download_link != '':
                res_info['link'] = resource.download_link

        result['resources'].append(res_info)

    # Load offering description
    parser = USDLParser(json.dumps(offering.offering_description), 'application/json')
    result['offering_description'] = parser.parse()

    if state == 'purchased' or state == 'rated':
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


def _get_purchased_offerings(user, db, pagination=None):

    # Get the user profile purchased offerings
    user_profile = db.wstore_userprofile.find_one({'user_id': ObjectId(user.pk)})
    # Get the user organization purchased offerings
    organization = db.wstore_organization.find_one({'_id': user_profile['organization_id']})

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

    return user_purchased


# Gets a set of offerings depending on filter value
def get_offerings(user, filter_='published', owned=False, pagination=None):

    if pagination and (not int(pagination['skip']) > 0 or not int(pagination['limit']) > 0):
        raise Exception('Invalid pagination limits')

    # Get all the offerings owned by the provider using raw mongodb access
    connection = MongoClient()
    db = connection[settings.DATABASES['default']['NAME']]
    offerings = db.wstore_offering
    # Pagination: define the first element and the number of elements
    if owned:
        if  filter_ == 'uploaded':
            prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id), 'state': 'uploaded'}).sort('_id', 1)
        elif filter_ == 'all':
            prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id)}).sort('_id', 1)
        elif  filter_ == 'published':
            prov_offerings = offerings.find({'owner_admin_user_id': ObjectId(user.id), 'state': 'published'}).sort('_id', 1)
        elif filter_ == 'purchased':
            if pagination:
                prov_offerings = _get_purchased_offerings(user, db, pagination)
                pagination = None
            else:
                prov_offerings = _get_purchased_offerings(user, db)

    else:
        if  filter_ == 'published':
            prov_offerings = offerings.find({'state': 'published'}).sort('_id', 1)

    if pagination:
        prov_offerings = prov_offerings.skip(int(pagination['skip']) - 1).limit(int(pagination['limit']))

    result = []

    for offer in prov_offerings:
        if '_id' in offer:
            pk = str(offer['_id'])
        else:
            pk = offer

        offering = Offering.objects.get(pk=pk)
        # Use get_offering_info to create the JSON with the offering info
        result.append(get_offering_info(offering, user))

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


# Creates a new offering including the media files and
# the repository uploads
@OfferingRollback
def create_offering(provider, profile, json_data):

    data = {}
    if not 'name' in json_data or not 'version' in json_data:
        raise Exception('Missing required fields')

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

    # Check the URL to notify the provider
    notification_url = ''

    if 'notification_url' in json_data:
        if json_data['notification_url'] == 'default':
            notification_url = profile.organization.notification_url
            if notification_url == '':
                raise Exception('No default URL defined for the organization')
        else:
            notification_url = json_data['notification_url']

    # Create the directory for app media
    dir_name = organization.name + '__' + data['name'] + '__' + data['version']
    path = os.path.join(settings.MEDIA_ROOT, dir_name)
    os.makedirs(path)
    image = json_data['image']

    # Save the application image or logo
    f = open(os.path.join(path, image['name']), "wb")
    dec = base64.b64decode(image['data'])
    f.write(dec)
    f.close()

    data['image_url'] = settings.MEDIA_URL + dir_name + '/' + image['name']
    # Save screen shots
    if 'related_images' in json_data:
        for image in json_data['related_images']:

            # images must be encoded in base64 format
            f = open(os.path.join(path, image['name']), "wb")
            dec = base64.b64decode(image['data'])
            f.write(dec)
            f.close()

            data['related_images'].append(settings.MEDIA_URL + dir_name + '/' + image['name'])

    # Save USDL document
    # If the USDL itself is provided

    if 'offering_description' in json_data:
        usdl_info = json_data['offering_description']

        repository = Repository.objects.get(name=json_data['repository'])
        repository_adaptor = RepositoryAdaptor(repository.host, 'storeOfferingCollection')
        offering_id = organization.name + '__' + data['name'] + '__' + data['version']

        usdl = usdl_info['data']
        data['description_url'] = repository_adaptor.upload(usdl_info['content_type'], usdl_info['data'], name=offering_id)

    # If the USDL is already uploaded in the repository
    elif 'description_url' in json_data:

        # Check that the link to USDL is unique since could be used to
        # purchase offerings from Marketplace
        usdl_info = {}
        usdl_url = json_data['description_url']
        off = Offering.objects.filter(description_url=usdl_url)

        if len(off) != 0:
            raise Exception('The provided USDL description is already registered')

        # Download the USDL from the repository
        repository_adaptor = RepositoryAdaptor(usdl_url)
        accept = "text/plain; application/rdf+xml; text/turtle; text/n3"

        usdl = repository_adaptor.download(content_type=accept)
        usdl_info['content_type'] = usdl['content_type']

        usdl = usdl['data']
        data['description_url'] = usdl_url

    else:
        raise Exception('No USDL description provided')

    # Serialize and store USDL info in json-ld format
    graph = rdflib.Graph()
    rdf_format = usdl_info['content_type']

    if rdf_format == 'text/turtle' or rdf_format == 'text/plain':
            rdf_format = 'n3'
    elif rdf_format == 'application/json':
            rdf_format = 'json-ld'

    graph.parse(data=usdl, format=rdf_format)
    data['offering_description'] = graph.serialize(format='json-ld', compact=True)

    # Create the offering
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
        offering_description=json.loads(data['offering_description']),
        notification_url=notification_url,
        creation_date=datetime.now()
    )

    # Load offering document to the search index
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    search_engine = SearchEngine(index_path)
    search_engine.create_index(offering)


def update_offering(offering, data):

    # Check if the offering has been published,
    # if published the offering cannot be updated
    if offering.state != 'uploaded':
        raise Exception('The offering cannot be edited')

    dir_name = offering.owner_organization + '__' + offering.name + '__' + offering.version
    path = os.path.join(settings.MEDIA_ROOT, dir_name)

    # Update the logo
    if 'image' in data:
        logo_path = offering.image_url
        logo_path = os.path.join(settings.BASEDIR, logo_path[1:])

        # Remove the old logo
        os.remove(logo_path)

        # Save the new logo
        f = open(os.path.join(path, data['image']['name']), "wb")
        dec = base64.b64decode(data['image']['data'])
        f.write(dec)
        f.close()
        offering.image_url = settings.MEDIA_URL + dir_name + '/' + data['image']['name']

    # Update the related images
    if 'related_images' in data:

        # Delete old related images
        for img in offering.related_images:
            old_image = os.path.join(settings.BASEDIR, img[1:])
            os.remove(old_image)

        offering.related_images = []

        # Create new images
        for img in data['related_images']:
            f = open(os.path.join(path, img['name']), "wb")
            dec = base64.b64decode(img['data'])
            f.write(dec)
            f.close()
            offering.related_images.append(settings.MEDIA_URL + dir_name + '/' + img['name'])

    new_usdl = False
    # Update the USDL description
    if 'offering_description' in data:
        usdl_info = data['offering_description']

        repository_adaptor = RepositoryAdaptor(offering.description_url)

        usdl = usdl_info['data']
        repository_adaptor.upload(usdl_info['content_type'], usdl)
        new_usdl = True

    # The USDL document has changed in the repository
    elif 'description_url' in data:
        usdl_info = {}
        usdl_url = data['description_url']

        # Check the link
        if usdl_url != offering.description_url:
            raise Exception('The provided USDL URL is not valid')

        # Download new content
        repository_adaptor = RepositoryAdaptor(usdl_url)
        accept = "text/plain; application/rdf+xml; text/turtle; text/n3"
        usdl = repository_adaptor.download(content_type=accept)

        usdl_info['content_type'] = usdl['content_type']
        usdl = usdl['data']

        new_usdl = True

    # If the USDL has changed store the new description
    # in the offering model
    if new_usdl:
        # Serialize and store USDL info in json-ld format
        graph = rdflib.Graph()

        rdf_format = usdl_info['content_type']

        if usdl_info['content_type'] == 'text/turtle' or usdl_info['content_type'] == 'text/plain':
            rdf_format = 'n3'
        elif usdl_info['content_type'] == 'application/json':
            rdf_format = 'json-ld'

        graph.parse(data=usdl, format=rdf_format)
        offering.offering_description = json.loads(graph.serialize(format='json-ld', compact=True))

    offering.save()


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
    offering.publication_date = datetime.now()
    offering.save()


def delete_offering(offering):
    # If the offering has been purchased it is not deleted
    # it is marked as deleted in order to allow customers that
    # have purchased the offering to install it if needed

    #delete the usdl description from the repository
    if offering.state == 'deleted':
        raise Exception('The offering is already deleted')

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

        context = Context.objects.all()[0]
        # Check if the offering is in the newest list
        if offering.pk in context.newest:
            # Remove the offering from the newest list
            newest = context.newest

            if len(newest) < 4:
                newest.remove(offering.pk)
            else:
                # Get the 4 newest offerings using the publication date for sorting
                connection = MongoClient()
                db = connection[settings.DATABASES['default']['NAME']]
                offerings = db.wstore_offering
                newest_off = offerings.find({'state': 'published'}).sort('publication_date', -1).limit(4)

                newest = []
                for n in newest_off:
                    newest.append(str(n['_id']))

            context.newest = newest
            context.save()

        # Check if the offering is in the top rated list
        if offering.pk in context.top_rated:
            # Remove the offering from the top rated list
            top_rated = context.top_rated
            if len(top_rated) < 4:
                top_rated.remove(offering.pk)
            else:
                # Get the 4 top rated offerings
                connection = MongoClient()
                db = connection[settings.DATABASES['default']['NAME']]
                offerings = db.wstore_offering
                top_off = offerings.find({'state': 'published', 'rating': {'$gt': 0}}).sort('rating', -1).limit(4)

                top_rated = []
                for t in top_off:
                    top_rated.append(str(t['_id']))

            context.top_rated = top_rated
            context.save()


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


def comment_offering(offering, comment, user):

    # Check if the user can comment the offering.
    if ((not offering.pk in user.userprofile.offerings_purchased) and \
    (not offering.pk in user.userprofile.organization.offerings_purchased)) or \
    offering.pk in user.userprofile.rated_offerings:
        raise Exception('The user cannot comment this offering')

    # Check comment structure
    if not 'title' in comment or not 'rating' in comment or not 'comment' in comment:
        raise Exception('Invalid comment')

    # Check rating
    if comment['rating'] < 0 or comment['rating'] > 5:
        raise Exception('Invalid rating')

    # Add the comment
    offering.comments.insert(0, {
        'user': user.username,
        'timestamp': str(datetime.now()),
        'title': comment['title'],
        'comment': comment['comment'],
        'rating': comment['rating']
    })

    # Calculate new offering rate
    old_rate = offering.rating

    if old_rate == 0:
        offering.rating = comment['rating']
    else:
        offering.rating = ((old_rate * (len(offering.comments) - 1)) + comment['rating']) / len(offering.comments)

    offering.save()

    user.userprofile.rated_offerings.append(offering.pk)
    user.userprofile.save()

    # Check the top rated structure
    context = Context.objects.all()[0]

    top_rated = context.top_rated

    # If there is a place append the offering
    if len(top_rated) < 4:
        top_rated.append(offering.pk)
        context.top_rated = sorted(top_rated, key=lambda off: Offering.objects.get(pk=off).rating, reverse=True)
        context.save()
    else:

        pos = None
        i = 0
        found = False

        # Check if the new rating is bigger than any top rated
        while i < len(top_rated) and not found:
            if Offering.objects.get(pk=top_rated[i]).rating < offering.rating:
                pos = i
                found = True
            else:
                i += 1

        # If the new rating is a top rating append the offering
        if pos != None:
            top_rated.insert(pos, offering.pk)
            top_rated.remove(top_rated[-1])
            context.top_rated = top_rated
            context.save()
