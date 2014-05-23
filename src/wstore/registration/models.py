import datetime
import hashlib
import random
import re
import smtplib

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.timezone import now

from wstore.models import Context


KEY_LENGTH = 30


def create_activation_key(username):
    """
    """
    salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
    return hashlib.sha1(salt+username).hexdigest()[:KEY_LENGTH]


def search_sha1(activation_key):
    """
    """
    valid_regex = re.compile(r'^\w+$').search(activation_key)
    return valid_regex and len(activation_key) <= KEY_LENGTH


class ProfileManager(models.Manager):
    """
    """
    def activate_user(self, activation_key):
        """
        """
        if not search_sha1(activation_key):
            return
        try:
            self.delete_expired_keys()
            profile = self.get(activation_key=activation_key)
        except self.model.DoesNotExist:
            return
        user = profile.user
        user.is_active = True
        user.save()
        profile.delete()
        return user

    def create_profile(self, user):
        """
        """
        user.is_active = False
        user.save()
        activation_key = create_activation_key(user.username)
        profile = self.create(user=user, activation_key=activation_key)
        profile.send_activation_email()
        return profile

    def delete_expired_keys(self):
        """
        """
        for profile in self.all():
            if profile.activation_key_expired():
                profile.user.delete()


def send_mail_from_gmail(toaddr, subject, message):
    """
    """
    username = settings.WSTOREMAIL
    password = settings.WSTOREMAILPASS
    fromaddr = settings.WSTOREMAILUSER
    server = smtplib.SMTP(settings.SMTPSERVER)
    server.starttls()
    server.login(username, password)
    message = 'Subject:' + subject + message
    server.sendmail(fromaddr, toaddr, message)


class Profile(models.Model):
    """
    """
    user = models.ForeignKey(User, unique=True)
    activation_key = models.CharField(max_length=KEY_LENGTH)
    objects = ProfileManager()

    def __unicode__(self):
        return u'Profile for: %s' % (self.user)

    def activation_key_expired(self):
        """
        """
        expiration_date = datetime.timedelta(days=settings.ACTIVATION_DAYS)
        datetime_now = datetime.datetime.now()
        return self.user.date_joined + expiration_date <= datetime_now

    def send_activation_email(self):
        """
        """
        site = Context.objects.all()[0].site.domain
        if site.endswith('/'):
            site = site[:-1]

        context = {
            'activation_url': self.get_absolute_url(),
            'expiration_days': settings.ACTIVATION_DAYS,
            'site': site,
            'user': self.user,
        }
        subject = render_to_string(
            'registration/activation_email_subject.txt', context)
        message = render_to_string(
            'registration/activation_email_message.txt', context)
        send_mail_from_gmail(self.user.email, subject, message)

    def get_absolute_url(self):
        """
        """
        return reverse('activate', args=[self.activation_key])
