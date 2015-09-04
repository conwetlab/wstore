# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.

import os
from urllib2 import HTTPError

from django.conf import settings
from wstore.models import Offering, Resource


def rollback(provider, profile, json_data, msg):

    if msg.startswith('Missing required fields'):
        return

    # Check files
    dir_name = profile.current_organization.name + '__' + json_data['name'] + '__' + json_data['version']
    path = os.path.join(settings.MEDIA_ROOT, dir_name)

    if os.path.exists(path):
        # Remove all files and directory
        for file_ in os.listdir(path):
            file_path = os.path.join(path, file_)
            os.remove(file_path)

        os.rmdir(path)

    # Check if the offering has been created
    offering = Offering.objects.filter(owner_organization=profile.current_organization, name=json_data['name'], version=json_data['version'])

    if len(offering) > 0:
        offering = offering[0]

        # Check if the offering has been bound
        if len(offering.resources):
            for res in offering.resources:
                re = Resource.objects.get(pk=unicode(res))
                re.offerings.remove(offering.pk)
                re.save()

        offering.delete()


class OfferingRollback():

    _func = None

    def __init__(self, func):
        self._func = func

    def __call__(self, provider, json_data):

        try:
            self._func(provider, json_data)
        except HTTPError as e:
            rollback(provider, provider.userprofile, json_data, 'Http error')
            raise e
        except Exception as e:
            rollback(provider, provider.userprofile, json_data, unicode(e))
            raise e
