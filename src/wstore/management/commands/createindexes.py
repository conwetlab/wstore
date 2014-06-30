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

import os
from sys import stdin
from shutil import rmtree

from django.core.management.base import BaseCommand
from django.conf import settings

from wstore.models import Offering
from wstore.search.search_engine import SearchEngine

def read_from_cmd():
    return stdin.readline()[:-1]


class Command(BaseCommand):

    def handle(self, *args, **options):
        interactive = True

        if len(args) and args[0] == '--no-input':
            interactive = False

        # Ask the user if interactive
        if interactive:
            correct = False
            print "This process will delete the indexes directory. Continue: [y/n]"
            while not correct:
                opt = read_from_cmd()
                if opt != 'y' and opt != 'n':
                    print "Please include 'y' or 'n'"
                else:
                    correct = True

            if opt == 'n':
                return

        # Remove the index directory
        index_path = os.path.join(settings.BASEDIR, 'wstore')
        index_path = os.path.join(index_path, 'search')
        index_path = os.path.join(index_path, 'indexes')

        rmtree(index_path, True)

        # Generate new search indexes
        se = SearchEngine(index_path)
        for o in Offering.objects.all():
            se.create_index(o)
