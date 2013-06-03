
import json

import urllib2

from wstore.store_commons.utils.method_request import MethodRequest


def notify_provider(purchase):
    """
        This method is use to notify the service provider
        that his offering has been purchased
    """
    notification_url = purchase.offering.notification_url

    # FIXME Make the notification URL a mandatory field
    if notification_url != '':

        data = {
            'offering': {
                'organization': purchase.offering.owner_organization,
                'name': purchase.offering.name,
                'version': purchase.offering.version
            },
            'reference': purchase.ref,
            'customer': purchase.customer.username
        }

        body = json.dumps(data)
        headers = {'Content-type': 'application/json'}

        request = MethodRequest('POST', notification_url, body, headers)

        opener = urllib2.build_opener()

        try:
            response = opener.open(request)
        except:
            pass
