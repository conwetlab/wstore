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
import json
import lucene
import rdflib
from lucene import SimpleFSDirectory, File, Document, Field, \
StandardAnalyzer, IndexWriter, Version, IndexSearcher, QueryParser

from wstore.models import Offering


class SearchEngine():

    _index_path = None

    def __init__(self, index_path):
        self._index_path = index_path

    def _aggregate_text(self, offering):

        usdl_document = offering.offering_description
        graph = rdflib.Graph()

        graph.parse(data=json.dumps(usdl_document), format='json-ld')

        text = ''

        for s, p, o in graph:
            if isinstance(o, rdflib.Literal):
                text += ' ' + str(o)

        return text

    def create_index(self, offering):

        # initialize java VM for lucene
        lucene.getVMEnv().attachCurrentThread()

        # Check if the index already exists to avoid overwrite it
        create = False

        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            create = True

        # Open the index
        index = SimpleFSDirectory(File(self._index_path))

        analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)

        index_writer = IndexWriter(index, analyzer, create, IndexWriter.MaxFieldLength.UNLIMITED)

        # Aggregate all the information included in the USDL document in
        # a single string in order to add a new document to the index
        text = self._aggregate_text(offering)

        # Add the new document
        document = Document()

        document.add(Field("content", text, Field.Store.YES, Field.Index.ANALYZED))
        document.add(Field("id", offering.pk, Field.Store.YES, Field.Index.NOT_ANALYZED))
        index_writer.addDocument(document)

        # Optimize the index
        index_writer.optimize()

        # Close the index
        index_writer.close()

    def full_text_search(self, user, text, state=None, count=False, pagination=None, sort=None):

        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            raise Exception('The index not exist')

        # Get the index reader
        lucene.getVMEnv().attachCurrentThread()
        index = SimpleFSDirectory(File(self._index_path))
        analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        lucene_searcher = IndexSearcher(index)

        # perform the query
        query = QueryParser(Version.LUCENE_CURRENT, 'content', analyzer).parse(text)

        max_number = 1000
        total_hits = lucene_searcher.search(query, max_number)

        result = []
        # The get_offering_info method is imported inside this method in order to avoid a cross-reference import error
        from wstore.offerings.offerings_management import get_offering_info

        i = 0
        for hit in total_hits.scoreDocs:
            doc = lucene_searcher.doc(hit.doc)

            # Get the offerings
            offering = Offering.objects.get(pk=doc.get('id'))
            offering_info = get_offering_info(offering, user)

            # filter the offerings
            # if no state provided means that all published offerings are wanted
            if state == None:
                if offering_info['state'] == 'published' or offering_info['state'] == 'purchased':
                    if not count:
                        result.append(offering_info)
                    else:
                        i += 1

            elif state == 'purchased':
                if offering_info['state'] == 'purchased':
                    if not count:
                        result.append(offering_info)
                    else:
                        i += 1

            elif state == 'all':
                if offering.owner_admin_user == user:
                    if not count:
                        result.append(offering_info)
                    else:
                        i += 1
            else:
                if offering.owner_admin_user == user and offering_info['state'] == state:
                    if not count:
                        result.append(offering_info)
                    else:
                        i += 1

        if count:
            result = {'number': i}
        elif pagination != None and len(result) > 0:
            # Check if it is possible to retrieve the requested page
            if pagination['start'] > len(result):
                raise Exception('Invalid page')

            result = result[pagination['start'] - 1: (pagination['limit'] + (pagination['start'] - 1))]

        # Check if is needed to sort the result
        rev = True
        if not count and sort:
            if sort == 'name':
                rev = False

            if sort == 'date':
                if state != 'all' or state != 'purchased':
                    sort = 'creation_date'
                else:
                    sort = 'publication_date'

            # Sort the result
            result = sorted(result, key=lambda off: off[sort], reverse=rev)

        return result
