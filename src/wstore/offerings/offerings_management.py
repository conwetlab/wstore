# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from __future__ import unicode_literals

import re
import base64
import os
from datetime import datetime
from bson.objectid import ObjectId
from copy import deepcopy

from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.repository_adaptor.repositoryAdaptor import repository_adaptor_factory, unreg_repository_adaptor_factory
from wstore.market_adaptor.marketadaptor import marketadaptor_factory
from wstore.search.search_engine import SearchEngine
from wstore.offerings.offering_rollback import OfferingRollback
from wstore.models import Offering, Resource, Repository
from wstore.models import Marketplace, MarketOffering
from wstore.models import Purchase
from wstore.models import UserProfile, Context
from wstore.store_commons.utils.version import is_lower_version
from wstore.store_commons.utils.name import is_valid_id
from wstore.store_commons.utils.url import is_valid_url
from wstore.social.tagging.tag_manager import TagManager
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.database import get_database_connection
from wstore.offerings.usdl.usdl_generator import USDLGenerator


def get_offering_info(offering, user):

    user_profile = UserProfile.objects.get(user=user)

    # Check if the user has purchased the offering
    state = offering.state

    # Check if the current organization is the user organization
    if user_profile.is_user_org():

        if offering.pk in user_profile.offerings_purchased:
            state = 'purchased'
            purchase = Purchase.objects.get(offering=offering, customer=user, organization_owned=False)

        if offering.pk in user_profile.rated_offerings:
            state = 'rated'

    else:
        if offering.pk in user_profile.current_organization.offerings_purchased:
            state = 'purchased'
            purchase = Purchase.objects.get(offering=offering, owner_organization=user_profile.current_organization)

        if user_profile.current_organization.has_rated_offering(user, offering):
            state = 'rated'

    # Load offering data
    result = {
        'name': offering.name,
        'owner_organization': offering.owner_organization.name,
        'owner_admin_user_id': offering.owner_admin_user.username,
        'version': offering.version,
        'state': state,
        'description_url': offering.description_url,
        'rating': "{:.2f}".format(offering.rating),
        'comments': offering.comments,
        'tags': offering.tags,
        'image_url': offering.image_url,
        'related_images': offering.related_images,
        'creation_date': str(offering.creation_date),
        'publication_date': str(offering.publication_date),
        'open': offering.open,
        'offering_description': offering.offering_description,
        'resources': []
    }

    # Load resources
    for res in offering.resources:
        resource = Resource.objects.get(pk=res)
        res_info = {
            'name': resource.name,
            'version': resource.version,
            'description': resource.description,
            'content_type': resource.content_type,
            'open': resource.open,
            'resource_type': resource.resource_type,
            'metadata': resource.meta_info
        }

        if (state == 'purchased' or state == 'rated' or offering.open):
            if resource.resource_path != '':
                res_info['link'] = resource.resource_path
            elif resource.download_link != '':
                res_info['link'] = resource.download_link

        result['resources'].append(res_info)

    # Load applications
    if settings.OILAUTH:
        result['applications'] = offering.applications

    if not offering.open and (state == 'purchased' or state == 'rated'):
        result['bill'] = purchase.bill

        # If the offering has been purchased the parsed pricing model is replaced
        # With the pricing model of the contract in order to included the extra info
        # needed such as renovation dates etc.

        if len(result['offering_description']['pricing']['price_plans']) > 0:

            pricing_model = purchase.contract.pricing_model
            related_plan = None

            if len(result['offering_description']['pricing']['price_plans']) > 1:
                # Search for the related plan
                for plan in result['offering_description']['pricing']['price_plans']:
                    if plan['label'].lower() == pricing_model['label']:
                        related_plan = deepcopy(plan)
            else:
                related_plan = deepcopy(result['offering_description']['pricing']['price_plans'][0])

            related_plan['price_components'] = []

            if 'subscription' in pricing_model:

                for subs in pricing_model['subscription']:
                    subs['renovation_date'] = str(subs['renovation_date'])
                    related_plan['price_components'].append(subs)

            if 'single_payment' in pricing_model:
                related_plan['price_components'].extend(pricing_model['single_payment'])

            if 'pay_per_use' in pricing_model:
                related_plan['price_components'].extend(pricing_model['pay_per_use'])

            result['offering_description']['pricing']['price_plans'] = [related_plan]

    return result


def _get_purchased_offerings(user, db, pagination=None, sort=None):

    # Get the user profile purchased offerings
    user_profile = db.wstore_userprofile.find_one({'user_id': ObjectId(user.pk)})
    # Get the user organization purchased offerings
    organization = db.wstore_organization.find_one({'_id': user_profile['current_organization_id']})

    if not user.userprofile.is_user_org():
        user_purchased = organization['offerings_purchased']
    else:
        # If the current organization is the user organization, load
        # all user offerings

        user_purchased = user_profile['offerings_purchased']

        # Append user offerings from organization offerings
        for offer in organization['offerings_purchased']:
            if offer not in user_purchased:
                user_purchased.append(offer)

    # Check sorting
    if sort == 'creation_date':
        user_purchased = sorted(user_purchased, key=lambda off: Offering.objects.get(pk=off).creation_date, reverse=True)
    elif sort == 'publication_date':
        user_purchased = sorted(user_purchased, key=lambda off: Offering.objects.get(pk=off).publication_date, reverse=True)
    elif sort == 'name':
        user_purchased = sorted(user_purchased, key=lambda off: Offering.objects.get(pk=off).name)
    elif sort == 'rating':
        user_purchased = sorted(user_purchased, key=lambda off: Offering.objects.get(pk=off).rating, reverse=True)

    # If pagination has been defined take the offerings corresponding to the page
    if pagination:
        skip = int(pagination['skip']) - 1
        limit = int(pagination['limit'])

        if skip < len(user_purchased):
            user_purchased = user_purchased[skip:(skip + limit)]
        else:
            user_purchased = []

    return user_purchased


# Gets a set of offerings depending on filter value
def get_offerings(user, filter_='published', state=None, pagination=None, sort=None):

    allowed_states = ['uploaded', 'published', 'deleted']

    if pagination and (not int(pagination['skip']) > 0 or not int(pagination['limit']) > 0):
        raise ValueError('Invalid pagination limits')

    # Validate states
    if state:
        for st in state:
            if st not in allowed_states:
                raise ValueError('Invalid state: ' + st)

    # Set sorting values
    order = -1
    if sort is None or sort == 'date':
        if filter_ == 'published' or filter_ == 'purchased':
            sorting = 'publication_date'
        else:
            sorting = 'creation_date'
    elif sort == 'popularity':
        sorting = 'rating'
    else:
        sorting = sort
        if sorting == 'name':
            order = 1

    # Get all the offerings owned by the provider using raw mongodb access
    db = get_database_connection()
    offerings = db.wstore_offering

    # Pagination: define the first element and the number of elements
    if filter_ == 'provided':
        current_organization = user.userprofile.current_organization
        query = {
            'owner_organization_id': ObjectId(current_organization.id),
            'state': {'$in': state}
        }

        prov_offerings = offerings.find(query).sort(sorting, order)

    elif filter_ == 'purchased':
        if pagination:
            prov_offerings = _get_purchased_offerings(user, db, pagination, sort=sorting)
            pagination = None
        else:
            prov_offerings = _get_purchased_offerings(user, db, sort=sorting)

    elif filter_ == 'published':
            prov_offerings = offerings.find({'state': 'published'}).sort(sorting, order)
    else:
        raise ValueError('Invalid filter: ' + filter_)

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


def count_offerings(user, filter_='published', state=None):

    # Validate states
    if state:
        if filter_ != 'provided':
            raise ValueError('Invalid filter: states are not allowed for filter ' + filter_)

        for st in state:
            if st not in ['uploaded', 'published', 'deleted']:
                raise ValueError('Invalid state: ' + st)

    if filter_ == 'provided':
        if not state:
            raise ValueError('The state is needed for provided filter')

        current_org = user.userprofile.current_organization
        count = Offering.objects.filter(owner_admin_user=user, state__in=state, owner_organization=current_org).count()

    elif filter_ == 'purchased':
        current_org = user.userprofile.current_organization
        count = len(current_org.offerings_purchased)
        if user.userprofile.is_user_org():
            count += len(user.userprofile.offerings_purchased)

    elif filter_ == 'published':
        count = Offering.objects.filter(state='published').count()
    else:
        raise ValueError('Invalid filter: ' + filter_)

    return {'number': count}


def _save_encoded_image(path, name, data):
    """
    Saves into the filesystem a base64 encoded image
    """
    f = open(os.path.join(path, name), "wb")
    dec = base64.b64decode(data)
    f.write(dec)
    f.close()


def _create_image(dir_name, path, image):
    if 'name' not in image or 'data' not in image:
        raise ValueError('Missing required field in image')

    # Save the application image or logo
    _save_encoded_image(path, image['name'], image['data'])
    return settings.MEDIA_URL + dir_name + '/' + image['name']


@OfferingRollback
def create_offering(provider, data):
    """
    Creates a new offering including the media files and
    the repository uploads
    """
    profile = provider.userprofile

    # Validate basic fields
    if 'name' not in data or 'version' not in data or 'offering_description' not in data \
            or 'image' not in data:

        missing_fields = ''

        if 'name' not in data:
            missing_fields += ' name'

        if 'version' not in data:
            missing_fields += ' version'

        if 'offering_description' not in data:
            missing_fields += ' offering_description'

        if 'image' not in data:
            missing_fields += ' image'

        raise ValueError('Missing required fields:' + missing_fields)

    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), data['version']):
        raise ValueError('Invalid version format')

    if not is_valid_id(data['name']):
        raise ValueError('Invalid name format')

    # Get organization
    organization = profile.current_organization

    # Check if the offering already exists
    if len(Offering.objects.filter(name=data['name'], owner_organization=organization, version=data['version'])) > 0:
        raise ConflictError('The offering ' + data['name'] + ' version ' + data['version'] + ' already exists')

    # Check if the version of the offering is lower than an existing one
    offerings = Offering.objects.filter(owner_organization=organization, name=data['name'])
    for off in offerings:
        if is_lower_version(data['version'], off.version):
            raise ValueError('A bigger version of the current offering exists')

    is_open = data.get('open', False)

    # If using the idm, get the applications from the request
    if settings.OILAUTH and 'applications' in data:
        # Validate application structure
        for app in data['applications']:
            if 'name' not in app or 'url' not in app or 'id' not in app or 'description' not in app:
                raise ValueError('Missing a required field in application definition')

    # Check the URL to notify the provider
    notification_url = ''
    if 'notification_url' in data:
        if data['notification_url'] == 'default':
            notification_url = organization.notification_url
            if not notification_url:
                raise ValueError('There is not a default notification URL defined for the organization ' + organization.name + '. To configure a default notification URL provide it in the settings menu')
        else:
            # Check the notification URL
            if not is_valid_url(data['notification_url']):
                raise ValueError("Invalid notification URL format: It doesn't seem to be an URL")

            notification_url = data['notification_url']

    # Create the directory for app media
    dir_name = organization.name + '__' + data['name'] + '__' + data['version']
    path = os.path.join(settings.MEDIA_ROOT, dir_name)
    os.makedirs(path)

    # Validate image format
    if not isinstance(data['image'], dict):
        raise TypeError('Invalid image type')

    data['image_url'] = _create_image(dir_name, path, data['image'])

    # Save screen shots
    screenshots = []
    if 'related_images' in data:
        for image in data['related_images']:
            screenshots.append(_create_image(dir_name, path, image))
    else:
        data['related_images'] = []

    # Validate the USDL
    data['open'] = is_open
    data['organization'] = organization

    # Create offering USDL
    offering_info = deepcopy(data['offering_description'])
    offering_info['image_url'] = data['image_url']
    offering_info['name'] = data['name']
    offering_info['version'] = data['version']
    offering_info['organization'] = organization.name
    offering_info['base_id'] = 'pk'

    created = datetime.now()
    offering_info['created'] = unicode(created)
    offering_info['modified'] = unicode(created)

    data['offering_description']['modified'] = unicode(created)

    usdl_generator = USDLGenerator()
    usdl_generator.validate_info(offering_info, organization, open_=is_open)

    # Create the offering
    offering = Offering(
        name=data['name'],
        owner_organization=organization,
        owner_admin_user=provider,
        version=data['version'],
        state='uploaded',
        resources=[],
        comments=[],
        tags=[],
        image_url=data['image_url'],
        related_images=screenshots,
        notification_url=notification_url,
        creation_date=created,
        open=is_open,
        offering_description=data['offering_description']
    )

    if settings.OILAUTH and 'applications' in data:
        offering.applications = data['applications']

    offering.save()

    offering.offering_description['base_id'] = offering.pk
    offering.save()

    if 'resources' in data and len(data['resources']) > 0:
        bind_resources(offering, data['resources'], profile.user)

    # Load offering document to the search index
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    search_engine = SearchEngine(index_path)
    search_engine.create_index(offering)


def update_offering(offering, data):

    # Check if the offering has been published,
    # if published the offering cannot be updated
    if offering.state != 'uploaded' and not offering.open:
        raise PermissionDenied('The offering cannot be edited')

    dir_name = offering.owner_organization.name + '__' + offering.name + '__' + offering.version
    path = os.path.join(settings.MEDIA_ROOT, dir_name)

    # Update the logo
    if 'image' in data:
        logo_path = offering.image_url
        logo_path = os.path.join(settings.BASEDIR, logo_path[1:])

        # Remove the old logo
        os.remove(logo_path)

        # Save the new logo
        _save_encoded_image(path, data['image']['name'], data['image']['data'])
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
            _save_encoded_image(path, img['name'], img['data'])
            offering.related_images.append(settings.MEDIA_URL + dir_name + '/' + img['name'])

    if 'offering_description' in data:
        # Create offering USDL
        offering_info = deepcopy(data['offering_description'])
        offering_info['image_url'] = offering.image_url
        offering_info['name'] = offering.name
        offering_info['version'] = offering.version
        offering_info['organization'] = offering.owner_organization.name
        offering_info['base_id'] = offering.pk

        offering_info['created'] = unicode(offering.creation_date)

        mod = unicode(datetime.now())
        offering_info['modified'] = mod

        usdl_generator = USDLGenerator()
        usdl_generator.validate_info(offering_info, offering.owner_organization, open_=offering.open)

        data['offering_description']['modified'] = mod
        offering.offering_description = data['offering_description']

        if offering.open and offering.state == 'published' and len(offering.description_url):
            repository_adaptor = unreg_repository_adaptor_factory(offering.description_url)
            repository_adaptor.upload(
                'application/rdf+xml',
                usdl_generator.generate_offering_usdl(offering)[0]
            )

    offering.save()

    # Update offering indexes
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    se = SearchEngine(index_path)
    se.update_index(offering)


def publish_offering(user, offering, data):

    # Validate data
    if 'marketplaces' not in data:
        raise ValueError('Publication error: missing required field, marketplaces')

    # Validate the state of the offering
    if not offering.state == 'uploaded':
        raise PermissionDenied('Publication error: The offering ' + offering.name + ' ' + offering.version + ' cannot be published')

    # Validate the offering has enough content to be published
    # Open offerings cannot be published in they do not contain
    # digital assets (applications or resources)
    if offering.open and not len(offering.resources) and not len(offering.applications):
        raise PermissionDenied('Publication error: Open offerings cannot be published if they do not contain at least a digital asset (resource or application)')

    # Check if it possible to publish the offering in a Marketplace
    if not len(Repository.objects.all()) > 0 and len(data['marketplaces']) > 0:
        raise PermissionDenied('Publication error: It is not possible to publish an offering in a Markteplace if no Repositories has been registered')

    # Upload the USDL description of the offering to the repository
    if len(Repository.objects.all()) > 0:
        repository = Repository.objects.get(is_default=True)

        # Generate the USDL of the offering
        generator = USDLGenerator()
        usdl, offering_uri = generator.generate_offering_usdl(offering)

        repository_adaptor = repository_adaptor_factory(repository)
        offering_id = offering.owner_organization.name + '__' + offering.name + '__' + offering.version

        repository_adaptor.set_uri(offering_uri)
        offering.description_url = repository_adaptor.upload('application/rdf+xml', usdl, name=offering_id)

    # Publish the offering in the selected marketplaces
    for market in data['marketplaces']:
        try:
            m = Marketplace.objects.get(name=market)
        except:
            raise ValueError('Publication error: The marketplace ' + market + ' does not exist')

        market_adaptor = marketadaptor_factory(m, user)
        offering_id = offering.owner_organization.name + ' ' + offering.name + ' ' + offering.version
        info = {
            'name': offering_id,
            'url': offering.description_url
        }

        off_market_name = market_adaptor.add_service(info)
        offering.marketplaces.append(MarketOffering(
            marketplace=m,
            offering_name=off_market_name
        ))

    offering.state = 'published'
    offering.publication_date = datetime.now()
    offering.save()

    # Update offering indexes
    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    se = SearchEngine(index_path)
    se.update_index(offering)


def _remove_offering(offering, se):
    # If the offering has media files delete them
    dir_name = offering.owner_organization.name + '__' + offering.name + '__' + offering.version
    path = os.path.join(settings.MEDIA_ROOT, dir_name)

    try:
        files = os.listdir(path)

        for f in files:
            file_path = os.path.join(path, f)
            os.remove(file_path)

        os.rmdir(path)
    except OSError:
        # An OS error means that offering files
        # does not exist so continue with the deletion
        pass

    # Remove the search index
    se.remove_index(offering)

    # Remove the offering ID from the tag indexes
    if len(offering.tags):
        tm = TagManager()
        tm.delete_tag(offering)

    # Remove the offering pk from the bound resources
    for res in offering.resources:
        resource = Resource.objects.get(pk=unicode(res))
        resource.offerings.remove(offering.pk)
        resource.save()

    offering.delete()


def delete_offering(user, offering):
    # If the offering has been purchased it is not deleted
    # it is marked as deleted in order to allow customers that
    # have purchased the offering to install it if needed

    # delete the usdl description from the repository
    if offering.state == 'deleted':
        raise PermissionDenied('The offering is already deleted')

    if offering.state == 'published':
        repository_adaptor = unreg_repository_adaptor_factory(offering.description_url)
        repository_adaptor.set_credentials(user.userprofile.access_token)
        repository_adaptor.delete()

    index_path = os.path.join(settings.BASEDIR, 'wstore')
    index_path = os.path.join(index_path, 'search')
    index_path = os.path.join(index_path, 'indexes')

    se = SearchEngine(index_path)

    if offering.state == 'uploaded':
        _remove_offering(offering, se)
    else:
        offering.state = 'deleted'
        offering.save()

        # Delete the offering from marketplaces
        for market in offering.marketplaces:
            market_adaptor = marketadaptor_factory(market.marketplace, user)
            market_adaptor.delete_service(market.offering_name)

        # Update offering indexes
        if not offering.open:
            se.update_index(offering)

        context = Context.objects.all()[0]
        # Check if the offering is in the newest list
        if offering.pk in context.newest:
            # Remove the offering from the newest list
            newest = context.newest

            if len(newest) < 8:
                newest.remove(offering.pk)
            else:
                # Get the 8 newest offerings using the publication date for sorting
                db = get_database_connection()
                offerings = db.wstore_offering
                newest_off = offerings.find({'state': 'published'}).sort('publication_date', -1).limit(8)

                newest = []
                for n in newest_off:
                    newest.append(str(n['_id']))

            context.newest = newest
            context.save()

        # Check if the offering is in the top rated list
        if offering.pk in context.top_rated:
            # Remove the offering from the top rated list
            top_rated = context.top_rated
            if len(top_rated) < 8:
                top_rated.remove(offering.pk)
            else:
                # Get the 4 top rated offerings
                db = get_database_connection()
                offerings = db.wstore_offering
                top_off = offerings.find({'state': 'published', 'rating': {'$gt': 0}}).sort('rating', -1).limit(8)

                top_rated = []
                for t in top_off:
                    top_rated.append(str(t['_id']))

            context.top_rated = top_rated
            context.save()

        if offering.open:
            _remove_offering(offering, se)


def bind_resources(offering, data, provider):

    # Check that the offering supports binding
    if offering.state != 'uploaded' and not (offering.open and offering.state == 'published'):
        raise PermissionDenied('This offering cannot be modified')

    added_resources = []
    offering_resources = []
    for of_res in offering.resources:
        offering_resources.append(of_res)

    for res in data:
        try:
            resource = Resource.objects.get(name=res['name'], version=res['version'], provider=provider.userprofile.current_organization)
        except:
            raise ValueError('Resource not found: ' + res['name'] + ' ' + res['version'])

        # Check resource state
        if resource.state == 'deleted':
            raise PermissionDenied('Invalid resource, the resource ' + res['name'] + ' ' + res['version'] + ' is deleted')

        # Check open
        if not resource.open and offering.open:
            raise PermissionDenied('It is not allowed to include not open resources in an open offering')

        if not ObjectId(resource.pk) in offering_resources:
            added_resources.append(resource.pk)
        else:
            offering_resources.remove(ObjectId(resource.pk))

    # added_resources contains the resources to be added to the offering
    # and offering_resources the resources to be deleted from the offering

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

    offering.offering_description['modified'] = unicode(datetime.now())
    offering.save()

    # Update USDL document if needed
    if offering.open and offering.state == 'published' and len(offering.description_url):
        usdl_generator = USDLGenerator()
        repository_adaptor = unreg_repository_adaptor_factory(offering.description_url)
        repository_adaptor.upload(
            'application/rdf+xml',
            usdl_generator.generate_offering_usdl(offering)[0]
        )
