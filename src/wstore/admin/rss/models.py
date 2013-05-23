
from django.db import models


class RSS(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=100)
    correlation_number = models.IntegerField(default=0)

    class Meta:
        app_label = 'wstore'
