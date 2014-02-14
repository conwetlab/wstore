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
from os import path
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from stemming.porter2 import stem

from wstore.models import Offering


class TagManager():

    _index_path = None

    def __init__(self, index_path=None):
        # Check tag indexes path
        if not index_path:

            from django.conf import settings
            base = settings.BASEDIR
            self._index_path = path.join(base, 'wstore')
            self._index_path = path.join(self._index_path, 'social')
            self._index_path = path.join(self._index_path, 'indexes')
        else:
            self._index_path = index_path

    def update_tags(self, offering, tags):
        # Save offering tags
        offering.tags = tags
        offering.save()

        # Check if the index exists
        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            # Create dir if needed
            if not os.path.exists(self._index_path):
                os.makedirs(self._index_path)
            # Create schema
            schema = Schema(id=ID(stored=True, unique=True), tags=TEXT(stored=True))
            # Create index
            index = create_in(self._index_path, schema)
        else:
            index = open_dir(self._index_path)

        text = ''
        # Create tags text
        for tag in tags:
            text += stem(tag) + ' '

        # Check if the document exists
        with index.searcher() as searcher:
            query = QueryParser('id', index.schema).parse(unicode(offering.pk))

            index_writer = index.writer()
            if not len(searcher.search(query)):
                # Add new document
                index_writer.add_document(id=unicode(offering.pk), tags=unicode(text[:-1]))
            else:
                # Update the index
                index_writer.update_document(id=unicode(offering.pk), tags=unicode(text[:-1]))

            index_writer.commit()

    def search_by_tag(self, tag):
        # Get documents
        docs = self.get_index_doc_by_tag(tag)
        # Get offerings
        return [Offering.objects.get(doc['id']) for doc in docs]

    def get_index_doc_by_tag(self, tag):
        # Open the index
        index = open_dir(self._index_path)
        # Build the query
        query = QueryParser('tags', index.schema).parse(unicode(stem(tag)))
        # Get documents
        with index.searcher() as searcher:
            documents = searcher.search(query)
            doc_list = [{'id': doc['id'], 'tags': doc['tags']} for doc in documents]

        return doc_list