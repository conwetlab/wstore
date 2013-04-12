from paypalpy import paypal

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
from django.shortcuts import render

from fiware_store.store_commons.resource import Resource
from fiware_store.store_commons.utils.http import build_error_response, supported_request_mime_types
from fiware_store.models import Purchase
from fiware_store.models import UserProfile
from fiware_store.models import Organization
from fiware_store.charging_engine.charging_engine import ChargingEngine


class ServiceRecordCollection(Resource):

    # This method is used to load SDR documents and
    # start the charging process
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json',))
    def create(self, request):
        # Extract SDR document from the HTTP request
        # Call the charging engine core with the SDR
        # Return response
        pass


class PayPalConfirmation(Resource):

    # This method is used to receive the PayPal confirmation
    # when the customer is paying using his PayPal account
    def read(self, request, reference):
        try:
            token = request.GET.get('token')
            payer_id = request.GET.get('PayerID')

            pp = paypal.PayPal(settings.PAYPAL_USER, settings.PAYPAL_PASSWD, settings.PAYPAL_SIGNATURE, settings.PAYPAL_URL)

            purchase = Purchase.objects.get(pk=reference)
            pending_info = purchase.contract.pending_payment

            pp.DoExpressCheckoutPayment(
                paymentrequest_0_paymentaction='Sale',
                paymentrequest_0_amt=pending_info['price'],
                paymentrequest_0_currencycode='EUR',
                token=token,
                payerid=payer_id
            )
            charging_engine = ChargingEngine(purchase)
            charging_engine.end_charging(pending_info['price'], pending_info['concept'], pending_info['related_model'])
        except:
            return build_error_response(request, 400, 'Invalid request')

        # Check if is the first payment
        if len(purchase.contract.charges) == 1:
            # Add the offering to the user profile
            user_profile = UserProfile.objects.get(user=purchase.customer)
            user_profile.offerings_purchased.append(purchase.offering.pk)

            if purchase.organization_owned:
                org = Organization.objects.get(name=purchase.owner_organization)
                org.offerings_purchased.append(purchase.offering.pk)

        # Return the confirmation web page
        return render(request, 'store/paypal_confirmation_template.html')


class PayPalCancelation(Resource):

    # This method is used when the user cancel a charge
    # when is using a PayPal account
    @method_decorator(login_required)
    def read(self, request, reference):
        pass
