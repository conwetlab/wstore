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
from djangotoolbox.fields import ListField, DictField

from wstore.models import Purchase


class Contract(models.Model):
    # Parsed version of the pricing model used to calculate charges
    pricing_model = DictField()
    # Date of the last charge to the customer
    last_charge = models.DateTimeField(blank=True, null=True)
    # List with the made charges
    charges = ListField()
    # List with the charged SDRs for that offering
    applied_sdrs = ListField()
    # List the pending SDRs for that offering
    pending_sdrs = ListField()
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
    # Period of time defined by the unit for subscription models
    renovation_period = models.IntegerField(null=True, blank=True)
