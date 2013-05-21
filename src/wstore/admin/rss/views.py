import json

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_error_response, supported_request_mime_types
from wstore.models import RSS


class RSSCollection(Resource):

    @method_decorator(login_required)
    def read(self, request):

        response = []

        for rss in RSS.objects.all():
            response.append({
                'name': rss.name,
                'host': rss.host
            })

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        # Only the admin can register new RSS instances
        if not request.user.is_staff:
            return build_error_response(request, 403, 'Forbidden')

        data = json.loads(request.raw_post_data)

        if not 'name' in data and not 'host' in data:
            return build_error_response(request, 400, 'Invalid JSON content')

        # Check if the information provided is not already registered
        if len(RSS.objects.filter(name=data['name'])) > 0 or \
        len(RSS.objects.filter(name=data['name'])) > 0:
            return build_error_response(request, 400, 'Invalid JSON content')

        # Create the new entry
        RSS.objects.create(name=data['name'], host=data['host'])

        return build_error_response(request, 201, 'Created')


class RSSEntry(Resource):

    @method_decorator(login_required)
    def read(self, request, rss):

        try:
            rss_model = RSS.objects.get(name=rss)
            response = {
                'name': rss_model.name,
                'host': rss_model.host
            }
        except:
            return build_error_response(request, 400, 'Invalid request')

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @method_decorator(login_required)
    def delete(self, request, rss):

        if not request.user.is_staff:
            return build_error_response(request, 403, 'Forbidden')

        try:
            rss_model = RSS.objects.get(name=rss)
            rss_model.delete()
        except:
            return build_error_response(request, 400, 'Invalid request')

        return build_error_response(request, 204, 'No content')
