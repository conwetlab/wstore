import json

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.http import HttpResponse

from wstore.store_commons.utils.http import build_error_response, supported_request_mime_types
from wstore.store_commons.resource import Resource
from wstore.models import UserProfile
from wstore.models import Organization


class UserProfileCollection(Resource):

    @method_decorator(login_required)
    def read(self, request):

        if not request.user.is_staff:
            return build_error_response(request, 403, 'Forbidden')

        response = []
        for user in User.objects.all():
            user_profile = {}
            user_profile['username'] = user.username
            user_profile['first_name'] = user.first_name
            user_profile['last_name'] = user.last_name

            profile = UserProfile.objects.get(user=user)
            user_profile['organization'] = profile.organization.name
            user_profile['tax_address'] = profile.tax_address
            user_profile['roles'] = profile.roles

            if user.is_staff:
                user_profile['roles'].append('admin')

            if 'number' in profile.payment_info:
                user_profile['payment_info'] = {}
                number = profile.payment_info['number']
                number = 'xxxxxxxxxxxx' + number[-4:]
                user_profile['payment_info']['number'] = number
                user_profile['payment_info']['type'] = profile.payment_info['type']
                user_profile['payment_info']['expire_year'] = profile.payment_info['expire_year']
                user_profile['payment_info']['expire_month'] = profile.payment_info['expire_month']

            response.append(user_profile)
        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        if not request.user.is_staff:
            return build_error_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)
        # Create the user
        try:
            user = User.objects.create(username=data['username'], first_name=data['first_name'], last_name=data['last_name'])

            if 'admin' in data['roles']:
                user.is_staff = True

            user.save()

            # Get the user profile
            user_profile = UserProfile.objects.get(user=user)
            org = Organization.objects.get(name=data['organization'])

            user_profile.organization = org

            if 'provider' in data['roles']:
                user_profile.roles.append('provider')

            if 'tax_address' in data:
                user_profile.tax_address = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'country': data['tax_address']['country']
                }
            if 'payment_info' in data:
                user_profile.payment_info = {
                    'type': data['payment_info']['type'],
                    'number': data['payment_info']['number'],
                    'expire_month': data['payment_info']['expire_month'],
                    'expire_year': data['payment_info']['expire_year']
                }

            user_profile.save()

        except:
            return build_error_response(request, 400, 'Invalid content')

        return build_error_response(request, 201, 'Created')


class UserProfileEntry(Resource):

    @method_decorator(login_required)
    def read(self, request, username):

        if not request.user.is_staff and not request.user.username == username:
            return build_error_response(request, 403, 'Forbidden')

        user = User.objects.get(username=username)
        user_profile = {}
        user_profile['username'] = user.username
        user_profile['first_name'] = user.first_name
        user_profile['last_name'] = user.last_name

        profile = UserProfile.objects.get(user=user)
        user_profile['organization'] = profile.organization.name
        user_profile['tax_address'] = profile.tax_address
        user_profile['roles'] = profile.roles

        if user.is_staff:
            user_profile['roles'].append('admin')

        if 'number' in profile.payment_info:
            user_profile['payment_info'] = {}
            number = profile.payment_info['number']
            number = 'xxxxxxxxxxxx' + number[-4:]
            user_profile['payment_info']['number'] = number
            user_profile['payment_info']['type'] = profile.payment_info['type']
            user_profile['payment_info']['expire_year'] = profile.payment_info['expire_year']
            user_profile['payment_info']['expire_month'] = profile.payment_info['expire_month']

        return HttpResponse(json.dumps(user_profile), status=200, mimetype='application/json')

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json',))
    def update(self, request, username):

        if not request.user.is_staff:
            return build_error_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)
        # Create the user
        try:
            user = User.objects.get(username=username)

            if 'admin' in data['roles']:
                user.is_staff = True

            if 'password' in data:
                user.set_password(data['password'])

            user.save()

            # Get the user profile
            user_profile = UserProfile.objects.get(user=user)
            org = Organization.objects.get(name=data['organization'])

            user_profile.organization = org

            if 'provider' in data['roles'] and (not 'provider' in user_profile.roles):
                user_profile.roles.append('provider')

            if 'tax_address' in data:
                user_profile.tax_address = {
                    'street': data['tax_address']['street'],
                    'postal': data['tax_address']['postal'],
                    'city': data['tax_address']['city'],
                    'country': data['tax_address']['country']
                }
            if 'payment_info' in data:
                user_profile.payment_info = {
                    'type': data['payment_info']['type'],
                    'number': data['payment_info']['number'],
                    'expire_month': data['payment_info']['expire_month'],
                    'expire_year': data['payment_info']['expire_year']
                }

            user_profile.save()

        except:
            return build_error_response(request, 400, 'Invalid content')

        return build_error_response(request, 200, 'OK')

    @method_decorator(login_required)
    def delete(self, request, username):
        pass


class OrganizationCollection(Resource):

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        if not request.user.is_staff:
            return build_error_response(request, 403, 'Forbidden')

        try:
            data = json.loads(request.raw_post_data)
            Organization.objects.create(name=data['name'])
        except:
            return build_error_response(request, 400, 'Inavlid content')

        return build_error_response(request, 201, 'Created')

    @method_decorator(login_required)
    def read(self, request):

        response = []

        for org in Organization.objects.all():
            response.append(org.name)

        return HttpResponse(json.dumps(response), status=200, mimetype='appliacation/json')
