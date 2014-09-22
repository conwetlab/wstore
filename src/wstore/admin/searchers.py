# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Polit?cnica de Madrid

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

import os

from django.conf import settings
from django.contrib.auth.models import User

from whoosh import index, fields
from whoosh.qparser import QueryParser


class UserSchema(fields.SchemaClass):

    pk = fields.ID(stored=True, unique=True)
    full_name = fields.TEXT(stored=True, spelling=True)
    username = fields.TEXT(stored=True, spelling=True)
    email = fields.TEXT(stored=True, spelling=True)
    content = fields.NGRAM(phrase=True)


class ResourceBrowser(object):

    stored_resources = {
        'user': {
            'model': User,
            'schema': UserSchema,
        },
    }

    @classmethod
    def add_resource(cls, indexname, fields=None, resource=None):

        if fields is None and resource is None:
            return None

        ix = cls.open_index(indexname)

        if resource is not None:
            fields = eval('cls()._build_' + indexname + '_fields')(resource)

        try:
            with ix.writer() as writer:
                writer.update_document(**fields)
        except:
            with ix.writer() as writer:
                writer.add_document(**fields)

    @classmethod
    def clear_index(cls, indexname, dirname=None):

        if dirname is None:
            dirname = settings.RESOURCE_INDEX_DIR

        if not os.path.exists(dirname):
            os.mkdir(dirname)

        if not indexname in cls.stored_resources:
            return None

        schema = cls.stored_resources[indexname]['schema']

        return index.create_in(dirname, schema(), indexname=indexname)

    @classmethod
    def get_resource_model(cls, indexname):

        if not indexname in cls.stored_resources:
            return None

        return cls.stored_resources[indexname]['model']

    @classmethod
    def is_stored(cls, indexname):

        return indexname in cls.stored_resources

    @classmethod
    def open_index(cls, indexname, dirname=None):

        if dirname is None:
            dirname = settings.RESOURCE_INDEX_DIR

        if not os.path.exists(dirname):
            os.mkdir(dirname)

        if not indexname in cls.stored_resources:
            return None

        if not index.exists_in(dirname, indexname=indexname):
            schema = cls.stored_resources[indexname]['schema']
            return index.create_in(dirname, schema(), indexname=indexname)

        return index.open_dir(dirname, indexname=indexname)

    @classmethod
    def search(cls, indexname, querytext):

        ix = cls.open_index(indexname)
        user_q = QueryParser('content', ix.schema).parse(querytext)
        search_result = {}

        with ix.searcher() as searcher:
            hits = searcher.search(user_q)
            search_result['results'] = [hit.fields() for hit in hits]

        return search_result

    def _build_user_fields(self, resource):

        fields = {
            'pk': '%s' % unicode(resource.pk),
            'full_name': '%s %s' % (unicode(resource.first_name), unicode(resource.last_name)),
            'username': '%s' % unicode(resource.username),
            'email': '%s' % unicode(resource.email),
            'content': '%s %s %s %s' % (unicode(resource.first_name), unicode(resource.last_name),
                unicode(resource.username), unicode(resource.email.split('@', 1)[0])),
        }

        return fields
