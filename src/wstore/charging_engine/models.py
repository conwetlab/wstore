from django.db import models
from djangotoolbox.fields import ListField, DictField

from wstore.models import Purchase


class Contract(models.Model):
    # Parsed version of the pricing model used to calculate charges
    pricing_model = DictField()
    # Date of the last charge to the customer
    last_charge = models.DateTimeField(blank=True, null=True)
    # List with the made charges
    charges = ListField()
    # List with the received SDRs for that offering
    applied_sdrs = ListField()
    # Related purchase
    purchase = models.OneToOneField(Purchase)
    # Pending paid info used in asynchronous charges
    pending_payment = DictField()


# This model is used as a unit dictionary in order to determine
# the pricing model that is being used
class Unit(models.Model):
    # Name of the unit
    name = models.CharField(max_length=50)
    # Type of price model defined by the unit
    defined_model = models.CharField(max_length=50)
