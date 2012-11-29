
from django.contrib.auth.models import User
from django.db import models
from djangotoolbox.fields import ListField, DictField


# An application is an offering composed by some
# backend comopents and some resources
class Application(models.Model):
    name = models.CharField(max_length=50)
    owner_organization = models.CharField(max_length=50)
    owner_admin_user = models.ForeignKey(User)
    # support_organization
    # support_admin_user
    version = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    description_url = models.CharField(max_length=200)
    resources = ListField()
    rating = models.FloatField(default=0)
    comments = ListField()
    tags = ListField()
    image_url = models.CharField(max_length=100)
    related_images = ListField()
    offering_description = DictField()

    def is_owner(self, user):
        return self.owner_admin_user == user

    class Meta:
        app_label = 'fiware_store'
        unique_together = ('name', 'owner_organization', 'version')


# The resources are the frontend components of an application
# a resource could be a web based component or an API used to
# access backend components
class Resource(models.Model):
    name = models.CharField(max_length=50)
    provider = models.ForeignKey(User)
    version = models.CharField(max_length=20)
    resource_type = models.CharField(max_length=50)
    description = models.TextField()
    state = models.CharField(max_length=50)
    image_url = models.CharField(max_length=100)
    related_elements = ListField()
    application = models.ForeignKey(Application)

    class Meta:
        app_label = 'fiware_store'
        unique_together = ('name', 'provider', 'version')
