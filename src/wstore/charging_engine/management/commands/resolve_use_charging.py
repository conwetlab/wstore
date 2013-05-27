import time

from datetime import datetime

from django.core.management.base import BaseCommand

from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.charging_engine.models import Contract
from wstore.models import Organization


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
            This method is used to perform the charging process
            of the offerings that have pending SDR for more than
            a month
        """
        import ipdb; ipdb.set_trace()
        now = time.mktime(datetime.now().timetuple())

        # Get contracts

        for contract in Contract.objects.all():

            pending_sdrs = contract.pending_sdrs

            if len(pending_sdrs) > 0:
                time_stamp = time.mktime(pending_sdrs[0]['time_stamp'].timetuple())

                if (time_stamp + 2592000) <= now:
                    # Get the related payment info
                    purchase = contract.purchase

                    if purchase.organization_owned:
                        org = Organization.objects.get(name=purchase.owner_organization)
                        payment_info = org.payment_info
                    else:
                        payment_info = purchase.customer.userprofile.payment_info

                    charging = ChargingEngine(purchase, payment_method='credit_card', credit_card=payment_info)
                    charging.resolve_charging(sdr=True)
