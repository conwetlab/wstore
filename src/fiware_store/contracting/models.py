
from django.db import models
from django.contrib.auth.models import User
from djangotoolbox.fields import DictField
from djangotoolbox.fields import ListField

from fiware_store.models import Offering


class Purchase(models.Model):

    ref = models.CharField(max_length=50)
    customer = models.ForeignKey(User)
    organization_owned = models.BooleanField()
    owner_organization = models.CharField(max_length=100)
    date = models.DateTimeField()
    offering = models.ForeignKey(Offering)
    state = models.CharField(max_length=50)
    bill = ListField()
    tax_address = DictField()

    class Meta:
        app_label = 'fiware_store'
