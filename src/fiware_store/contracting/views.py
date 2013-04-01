import json

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse


from fiware_store.store_commons.resource import Resource
from fiware_store.store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from fiware_store.contracting.purchases_management import create_purchase
from fiware_store.models import Offering
from fiware_store.models import Resource as store_resource


class PurchaseCollection(Resource):

    # Creates a new purchase resource
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):

        user = request.user
        content_type = get_content_type(request)[0]

        if content_type == 'application/json':

            try:
                data = json.loads(request.raw_post_data)
                if isinstance(data['offering'], dict):
                    id_ = data['offering']
                    offering = Offering.objects.get(owner_organization=id_['organization'], name=id_['name'], version=id_['version'])
                else:
                    offering = Offering.objects.get(description_url=data['offering'])

                if 'tax_address' in data:
                    purchase = create_purchase(user, offering, data['organization_owned'], data['tax_address'])
                else:
                    purchase = create_purchase(user, offering, data['organization_owned'])

            except:
                build_error_response(request, 400, 'Invalid json content')

        response = {}
        # Load download resources URL
        response['resources'] = []

        for res in offering.resources:
            r = store_resource.objects.get(pk=res)

            if r.resource_type == 'download':
                # Check if the resource has been uploaded to the store or is
                # in an external applications server
                if r.resource_path != '':
                    response['resources'].append(r.resource_path)
                elif r.download_link != '':
                    response['resources'].append(r.download_link)

        # Load bill URL
        response['bill'] = purchase.bill

        return HttpResponse(json.dumps(response), status=201, mimetype=content_type)


class PurchaseEntry(Resource):

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def update(self, request, purchase_id):
        pass
