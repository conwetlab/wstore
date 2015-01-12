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

from pymongo import MongoClient

from django.conf import settings


def get_database_connection():
    """
    Gets a raw database connection to MongoDB
    """
    # Get database info from settings
    database_info = settings.DATABASES['default']

    client = None
    # Create database connection
    if database_info['HOST'] and database_info['PORT']:
        client = MongoClient(database_info['HOST'], database_info['PORT'])
    elif database_info['HOST'] and not database_info['PORT']:
        client = MongoClient(database_info['HOST'])
    elif not database_info['HOST'] and database_info['PORT']:
        client = MongoClient('localhost', database_info['PORT'])
    else:
        client = MongoClient()


    db_name = database_info['NAME']
    db = client[db_name]

    #Authenticate if needed
    if database_info['USER'] and database_info['PASSWORD']:
        db.authenticate(database_info['USER'], database_info['PASSWORD'], mechanism='MONGODB-CR')

    return db
