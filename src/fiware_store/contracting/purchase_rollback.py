
from fiware_store.models import Purchase
from fiware_store.models import UserProfile
from fiware_store.models import Organization


# This class is used as a decorator to avoid inconsistent states in
# purchases models in case of Exception
class PurchaseRollback():
    _funct = None

    def _rollback(self, purchase):
        # Check organization owned
        if purchase.organization_owned:
            org = Organization.objects.get(name=purchase.owner_organization)
            org.offerings_purchased.remove(purchase.offering.pk)
            org.save()

        # Delete the offering from the user profile
        user_profile = UserProfile.objects.get(user=purchase.customer)
        user_profile.offerings_purchased.remove(purchase.offering.pk)
        user_profile.save()

        # Delete the contract
        try:
            purchase.contract.delete()
        except:  # The contract may have not been created
            pass
        # Delete the Purchase
        purchase.delete()

    def __init__(self, funct):
        self._funct = funct

    def __call__(self, user, offering, org_owned=False, payment_info=None):
        try:
            result = self._funct(user, offering, org_owned, payment_info)
        except Exception, e:
            if e.message != "This offering can't be purchased" and e.message != 'The offering has been already purchased'\
             and e.message != 'Invalid payment method':

                # Get the purchase
                if org_owned:
                    user_profile = UserProfile.objects.get(user=user)
                    purchase = Purchase.objects.get(owner_organization=user_profile.organization.name, offering=offering)
                else:
                    purchase = Purchase.objects.get(customer=user, offering=offering)
                self._rollback(purchase)

            raise e
        return result
