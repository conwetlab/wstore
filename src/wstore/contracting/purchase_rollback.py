
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore.models import Organization


def rollback(purchase):
    # If the purchase state is paid means that the purchase has been made
    # so the models must not be deleted
    if purchase.state != 'paid':

        # Check the payment has been made
        contract = True
        try:
            contr = purchase.contract
        except:
            contract = False

        to_del = True
        if contract:
            # If the charges field contains any charge means that it is not
            # the first charge so the models cannot be deleted
            if len(contr.charges) > 0:
                purchase.state = 'paid'
                purchase.save()
                to_del = False

        if to_del:
            # Check organization owned
            if purchase.organization_owned:
                org = Organization.objects.get(name=purchase.owner_organization)
                if purchase.offering.pk in org.offerings_purchased:
                    org.offerings_purchased.remove(purchase.offering.pk)
                    org.save()

            # Delete the offering from the user profile
            user_profile = UserProfile.objects.get(user=purchase.customer)
            if purchase.offering.pk in user_profile.offerings_purchased:
                user_profile.offerings_purchased.remove(purchase.offering.pk)
                user_profile.save()

            # Delete the contract
            if contract:
                purchase.contract.delete()
            # Delete the Purchase
            purchase.delete()


# This class is used as a decorator to avoid inconsistent states in
# purchases models in case of Exception
class PurchaseRollback():
    _funct = None

    def __init__(self, funct):
        self._funct = funct

    def __call__(self, user, offering, org_owned=False, payment_info={}):
        try:
            # Call the decorated function
            result = self._funct(user, offering, org_owned, payment_info)
        except Exception, e:
            if e.message != "This offering can't be purchased" and e.message != 'The offering has been already purchased'\
             and e.message != 'Invalid payment method' and e.message != 'Invalid credit card info':

                # Get the purchase
                if org_owned:
                    user_profile = UserProfile.objects.get(user=user)
                    purchase = Purchase.objects.get(owner_organization=user_profile.organization.name, offering=offering)
                else:
                    purchase = Purchase.objects.get(customer=user, offering=offering)
                rollback(purchase)

            raise e
        return result
