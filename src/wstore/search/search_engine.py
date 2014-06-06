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

from __future__ import unicode_literals

import os
import json
import rdflib
from whoosh.fields import Schema, TEXT
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

from wstore.models import Offering


class SearchEngine():

    _index_path = None

    def __init__(self, index_path):
        self._index_path = index_path

    def _aggregate_text(self, offering):

        usdl_document = offering.offering_description
        graph = rdflib.ConjunctiveGraph()

        graph.parse(data=json.dumps(usdl_document), format='json-ld')

        text = ''

        for s, p, o in graph:
            if isinstance(o, rdflib.Literal):
                text += ' ' + unicode(o)

        return text

    def create_index(self, offering):

        # Check if the index already exists to avoid overwrite it
        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            # Create dir if needed
            if not os.path.exists(self._index_path):
                os.makedirs(self._index_path)

            # Create schema
            schema = Schema(id=TEXT(stored=True), content=TEXT)
            # Create index
            index = create_in(self._index_path, schema)
        else:
            index = open_dir(self._index_path)

        # Open the index
        index_writer = index.writer()

        # Aggregate all the information included in the USDL document in
        # a single string in order to add a new document to the index
        text = self._aggregate_text(offering)

        # Add the new document
        index_writer.add_document(id=unicode(offering.pk), content=unicode(text))
        index_writer.commit()

    def full_text_search(self, user, text, state=None, count=False, pagination=None, sort=None):

        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            raise Exception('The index does not exist')

        # Get the index reader
        index = open_dir(self._index_path)

        with index.searcher() as searcher:

            # perform the query
            query = QueryParser('content', index.schema).parse(unicode(text))

            search_result = searcher.search(query, limit=None)

            result = []
            # The get_offering_info method is imported inside this method in order to avoid a cross-reference import error
            from wstore.offerings.offerings_management import get_offering_info

            i = 0
            for hit in search_result:

                # Get the offerings
                offering = Offering.objects.get(pk=hit['id'])
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
                    if (offering.owner_admin_user == user) and \
                    (offering.owner_organization == user.userprofile.current_organization):
                        if not count:
                            result.append(offering_info)
                        else:
                            i += 1
                else:
                    if (offering.owner_admin_user == user) and (offering_info['state'] == state) \
                    and (offering.owner_organization == user.userprofile.current_organization):
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
