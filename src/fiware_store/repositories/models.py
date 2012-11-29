
from django.db import models


class Repository(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=100)

    class Meta:
        app_label = 'fiware_store'
