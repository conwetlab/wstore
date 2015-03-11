# -*- coding: utf-8 -*-

# Copyright (c) 2013-2015 CoNWeT Lab., Universidad Politécnica de Madrid

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


from __future__ import unicode_literals

from wstore.store_commons.errors import ConflictError

from wstore.models import Repository


def register_repository(name, host, default=False):

    # Check if the repository name is in use
    repos = Repository.objects.filter(name=name) | Repository.objects.filter(host=host)

    if len(repos) > 0:
        raise ConflictError('The repository already exists')

    Repository.objects.create(name=name, host=host, is_default=default)


def unregister_repository(repository):
    rep = None
    try:
        rep = Repository.objects.get(name=repository)
    except:
        raise Exception('Not found')

    rep.delete()


def get_repositories():

    repositories = Repository.objects.all()
    response = []

    for rep in repositories:
        response.append({
            'name': rep.name,
            'host': rep.host
        })

    return response
