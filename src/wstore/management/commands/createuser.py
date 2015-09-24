
# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from wstore.models import User
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--staff',
                action='store_true',
                dest='staff',
                default=False,
                help="Whether the new user is staff"),
    )


    def handle(self, *args, **options):
        """
        Create a user
        """
        username = args[0]
        password = args[1]

        # Create the site
        user = User.objects.create_user(username=username, password=password)

        if options['staff']:
            user.is_staff = True
            user.save()

