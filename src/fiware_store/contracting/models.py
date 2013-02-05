
from django.db import models
from django.contrib.auth.models import User

from fiware_store.models import Offering


class Purchase(models.Model):

    ref = models.CharField(max_length=50)
    customer = models.ForeignKey(User)
    organization_owned = models.BooleanField()
    owner_organization = models.CharField(max_length=100)
    date = models.DateTimeField()
    offering = models.ForeignKey(Offering)
    state = models.CharField(max_length=50)
    bill = models.CharField(max_length=200)
    tax_address = models.TextField()

    class Meta:
        app_label = 'fiware_store'
