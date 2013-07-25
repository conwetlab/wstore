# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

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

from django.db import models
from django.contrib.auth.models import User
from djangotoolbox.fields import DictField
from djangotoolbox.fields import ListField

from wstore.models import Offering
from wstore.models import Organization


class Purchase(models.Model):

    ref = models.CharField(max_length=50)
    customer = models.ForeignKey(User)
    organization_owned = models.BooleanField()
    owner_organization = models.ForeignKey(Organization, null=True, blank=True)
    date = models.DateTimeField()
    offering = models.ForeignKey(Offering)
    state = models.CharField(max_length=50)
    bill = ListField()
    tax_address = DictField()

    class Meta:
        app_label = 'wstore'
