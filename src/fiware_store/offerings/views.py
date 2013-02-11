import json
from urllib2 import HTTPError

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.http import HttpResponse

from store_commons.resource import Resource
from store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from fiware_store.models import Offering
from fiware_store.models import UserProfile
from fiware_store.offerings.offerings_management import create_offering, get_offerings, get_offering_info, delete_offering, publish_offering, bind_resources
from fiware_store.offerings.resources_management import register_resource, get_provider_resources


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

        # Checks the provider role
        if 'provider' in profile.roles:

            if content_type == 'application/json':
                try:
                    json_data = json.loads(request.raw_post_data)
                    create_offering(user, profile, json_data)
                except HTTPError:
                    return build_error_response(request, 502, 'Bad Gateway')
                except:
                    return build_error_response(request, 400, 'Invalid content')
            else:
                pass  # TODO xml parsed
        else:
            pass

        return build_error_response(request, 201, 'Created')

    @method_decorator(login_required)
    def read(self, request):

        # TODO support for xml requests
        # Read the query string in order to know the filter and the page
        filter_ = request.GET.get('filter', 'published')
        user = User.objects.get(username=request.user)

        if filter_ == 'provider':
            # Get provider id
            result = get_offerings(user, request.GET.get('state'), owned=True)

        elif filter_ == 'published':
            result = get_offerings(user)

        elif filter_ == 'purchased':
            result = get_offerings(user, 'purchased', owned=True)

        mime_type = 'application/JSON; charset=UTF-8'
        return HttpResponse(json.dumps(result), status=200, mimetype=mime_type)


class OfferingEntry(Resource):

    @method_decorator(login_required)
    def read(self, request, organization, name, version):

        offering = Offering.objects.get(name=name, owner_organization=organization, version=version)
        result = get_offering_info(offering)

        return HttpResponse(json.dumps(result), status=200, mimetype='application/json; charset=UTF-8')

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def update(self, request, organization, name, version):
        pass

    @method_decorator(login_required)
    def delete(self, request, organization, name, version):
        # If the offering has been purchased it is not deleted
        # it is marked as deleted in order to allow customers that
        # have puerchased the offering to intall it if needed
        offering = Offering.objects.get(name=name, owner_organization=organization, version=version)
        if not offering.is_owner(request.user):
            build_error_response(request, 401, 'Unauthorized')

        delete_offering(offering)

        return build_error_response(request, 204, 'No content')


class ResourceCollection(Resource):

    # Creates a new resource asociated with an user
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)
        content_type = get_content_type(request)[0]

        if 'provider' in profile.roles:

            if content_type == 'application/json':
                try:
                    data = json.loads(request.raw_post_data)
                    register_resource(user, data)
                except:
                    return build_error_response(request, 400, 'Invalid JSON content')
            else:  # TODO parse xml request
                pass
        else:
            pass

        return build_error_response(request, 201, 'Created')

    @method_decorator(login_required)
    def read(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if 'provider' in profile.roles:
            response = get_provider_resources(request.user)

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')


class ResourceEntry(Resource):
    pass


class PublishEntry(Resource):

    # Publish the offering is some marketplaces
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request, organization, name, version):
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
                publish_offering(offering, data)
            except HTTPError:
                build_error_response(request, 502, 'Bad gateway')
            except:
                build_error_response(request, 400, 'Invalid JSON content')

        return build_error_response(request, 200, 'OK')


class BindEntry(Resource):

    # Binds resources with offerings
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request, organization, name, version):
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
                bind_resources(offering, data, request.user)
            except:
                build_error_response(request, 400, 'Invalid JSON content')

        return build_error_response(request, 200, 'OK')
