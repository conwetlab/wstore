import json
from urlparse import urlunparse, urlparse

from django.contrib.sites.models import get_current_site
from django.http import HttpResponse
from django.shortcuts import render

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types, \
authentication_required
from wstore.offerings.offerings_management import get_offering_info
from wstore.contracting.purchases_management import create_purchase
from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.models import Offering, Organization
from wstore.models import Purchase
from wstore.models import Resource as store_resource
from wstore.contracting.purchase_rollback import rollback
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class PurchaseFormCollection(Resource):

    @authentication_required
    @supported_request_mime_types(('application/json', ))
    def create(self, request):

        data = json.loads(request.raw_post_data)

        user_profile = request.user.userprofile

        # Get the offering
        if isinstance(data['offering'], dict):
            id_ = data['offering']
            offering = Offering.objects.get(owner_organization=id_['organization'], name=id_['name'], version=id_['version'])
        else:
            offering = Offering.objects.get(description_url=data['offering'])

        # Check that the user has not already purchased the offering
        if offering.pk in user_profile.offerings_purchased \
        or offering.pk in user_profile.organization.offerings_purchased:
            return build_error_response(request, 400, 'You have already purchased the offering')

        # Check that the offering can be purchased
        if offering.state != 'published':
            return build_error_response(request, 400, 'The offering cannot be purchased')

        pk = offering.pk
        site = get_current_site(request)
        site = urlparse(site.domain)
        query = 'ID=' + pk

        # Create the URL that shows the purchase form
        url = urlunparse((site[0], site[1], '/api/contracting/form', '', query, ''))

        response = {
            'url': url
        }

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')

    @method_decorator(login_required)
    def read(self, request):

        id_ = request.GET.get('ID')

        user_profile = request.user.userprofile

        # Load the offering info
        try:
            offering = Offering.objects.get(pk=id_)
        except:
            return build_error_response(request, 404, 'The offering not exists')
        offering_info = get_offering_info(offering, request.user)

        # Check that the user is not the owner of the offering

        if offering.owner_admin_user == request.user:
            return build_error_response(request, 400, 'You are the owner of the offering')

        # Check that the user has not already purchased the offering
        if offering.pk in user_profile.offerings_purchased \
        or offering.pk in user_profile.organization.offerings_purchased:
            return build_error_response(request, 400, 'You have already purchased the offering')

        # Check that the offering can be purchased
        if offering.state != 'published':
            return build_error_response(request, 400, 'The offering cannot be purchased')

        # Create the context
        context = {
            'offering_info': json.dumps(offering_info)
        }

        # Return the form to purchase the offering
        return render(request, 'store/purchase_form.html', context)


class PurchaseCollection(Resource):

    # Creates a new purchase resource
    @authentication_required
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
                # Check if the offering has been paid before the exception has been raised
                paid = False

                if data['organization_owned']:
                    if offering.pk in request.user.userprofile.organization.offerings_purchased:
                        paid = True
                        response_info = Purchase.objects.get(owner_organization=request.user.userprofile.organization.name, offering=offering)
                else:
                    if offering.pk in request.user.userprofile.offerings_purchased:
                        paid = True
                        response_info = Purchase.objects.get(customer=request.user, offering=offering)

                if not paid:
                    return build_error_response(request, 400, 'Invalid json content')

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

    @authentication_required
    def read(self, request):
        pass

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def update(self, request, reference):

        purchase = Purchase.objects.get(ref=reference)

        data = json.loads(request.raw_post_data)

        try:
            if data['method'] == 'paypal':
                charging_engine = ChargingEngine(purchase, payment_method='paypal')
            elif data['method'] == 'credit_card':

                # Get the payment info
                if 'credit_card' in data:
                    credit_card = data['credit_card']
                else:
                    if purchase.organization_owned:
                        org = Organization.objects.get(name=purchase.owner_organization)
                        credit_card = org.payment_info
                    else:
                        credit_card = purchase.customer.userprofile.payment_info
                charging_engine = ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card)

            charging_engine.resolve_charging()
        except:
            # Refresh the purchase info
            purchase = Purchase.objects.get(ref=reference)
            rollback(purchase)
            return build_error_response(request, 400, 'Invalid JSON content')

        return build_error_response(request, 200, 'OK')
