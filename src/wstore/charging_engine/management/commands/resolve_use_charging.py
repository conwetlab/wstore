import time

from datetime import datetime

from django.core.management.base import BaseCommand

from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.charging_engine.models import Contract
from wstore.models import Organization
from wstore.contracting.models import Purchase


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
            This method is used to perform the charging process
            of the offerings that have pending SDR for more than
            a month
        """
        now = time.mktime(datetime.now().timetuple())

        if len(args) == 0:
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

        elif len(args) == 1:
            # Get the purchase
            try:
                purchase = Purchase.objects.get(ref=args[0])
            except:
                raise Exception('The provided purchase does not exists')

            # Get the contract
            contract = purchase.contract

            # Check if there are pending SDRs
            if (len(contract.pending_sdrs) > 0):

                # Get payment info
                if purchase.organization_owned:
                    org = Organization.objects.get(name=purchase.owner_organization)
                    payment_info = org.payment_info
                else:
                    payment_info = purchase.customer.userprofile.payment_info

                charging = ChargingEngine(purchase, payment_method='credit_card', credit_card=payment_info)
                charging.resolve_charging(sdr=True)

            else:
                raise Exception('No accounting info in the provided purchase')
        else:
            raise Exception('Invalid number of arguments')
