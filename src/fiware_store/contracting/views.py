import json

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse


from fiware_store.store_commons.resource import Resource
from fiware_store.store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from fiware_store.contracting.purchases_management import create_purchase
from fiware_store.charging_engine.charging_engine import ChargingEngine
from fiware_store.models import Offering
from fiware_store.models import Purchase
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
                payment_info = {}

                if isinstance(data['offering'], dict):
                    id_ = data['offering']
                    offering = Offering.objects.get(owner_organization=id_['organization'], name=id_['name'], version=id_['version'])
                else:
                    offering = Offering.objects.get(description_url=data['offering'])

                if 'tax_address' in data:
                    payment_info['tax_address'] = data['tax_address']

                payment_info['payment_method'] = data['payment']['method']

                if 'credit_card' in data['payment']:
                    payment_info['credit_card'] = data['payment']['credit_card']

                response_info = create_purchase(user, offering, data['organization_owned'], payment_info)
            except:
                build_error_response(request, 400, 'Invalid json content')

        response = {}
        # If the value returned by the create_purchase method is a string means that
        # the purchase is not ended and need user confirmation. response_info contains
        # the URL where redirect the user
        if isinstance(response_info, str):
            response['redirection_link'] = response_info
            status = 200
        else:  # The purchase is finished so the download links are returned
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
            response['bill'] = response_info.bill
            status = 201

        return HttpResponse(json.dumps(response), status=status, mimetype=content_type)


class PurchaseEntry(Resource):

    @method_decorator(login_required)
    def read(self, request):
        pass

    @method_decorator(login_required)
    @supported_request_mime_types(('application/json',))
    def update(self, request, reference):

        purchase = Purchase.objects.get(ref=reference)

        data = json.loads(request.raw_post_data)

        try:
            if data['method'] == 'paypal':
                charging_engine = ChargingEngine(purchase, payment_method='paypal')
            elif data['method'] == 'credit_card':
                charging_engine = ChargingEngine(purchase, payment_method='credit_card', credit_card=data['credit_card'])

            charging_engine.resolve_charging()
        except:
            build_error_response(request, 400, 'Invalid JSON content')

        return build_error_response(request, 200, 'OK')
