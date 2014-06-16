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
from decimal import Decimal
from whoosh.fields import Schema, TEXT, NUMERIC, DATETIME, KEYWORD
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh import query

from wstore.models import Offering, Purchase


class SearchEngine():

    _index_path = None

    def __init__(self, index_path):
        self._index_path = index_path

    def _aggregate_text(self, offering):
        """
        Create a single string for creating the index by extracting text fields
        from the USDL document of the offering
        """

        usdl_document = offering.offering_description
        graph = rdflib.ConjunctiveGraph()

        graph.parse(data=json.dumps(usdl_document), format='json-ld')

        text = ''

        for s, p, o in graph:
            if isinstance(o, rdflib.Literal):
                text += ' ' + unicode(o)

        return text

    def _aggregate_purchasers(self, offering):
        purchases = Purchase.objects.filter(offering=offering)

        result = ''
        for p in purchases:
            result += p.owner_organization.pk + ','

        return result[:-1]

    def create_index(self, offering):
        """
        Create a document entry for the offering in the
        search index
        """

        # Check if the index already exists to avoid overwrite it
        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            # Create dir if needed
            if not os.path.exists(self._index_path):
                os.makedirs(self._index_path)

            # Create schema
            schema = Schema(
                id=TEXT(stored=True),
                owner=KEYWORD,
                content=TEXT,
                name=KEYWORD(sortable=True),
                popularity=NUMERIC(int, decimal_places=2, sortable=True, signed=False),
                date=DATETIME(sortable=True),
                state=KEYWORD,
                purchaser=KEYWORD
            )
            # Create index
            index = create_in(self._index_path, schema)
        else:
            index = open_dir(self._index_path)

        # Open the index
        index_writer = index.writer()

        # Aggregate all the information included in the USDL document in
        # a single string in order to add a new document to the index
        text = self._aggregate_text(offering)

        purchasers_text = self._aggregate_purchasers(offering)

        # Add the new document
        index_writer.add_document(
            id=unicode(offering.pk),
            owner=unicode(offering.owner_organization.pk),
            content=unicode(text),
            name=unicode(offering.name),
            popularity=Decimal(offering.rating),
            date=offering.creation_date,
            state=unicode(offering.state),
            purchaser=purchasers_text
        )
        index_writer.commit()

    def update_index(self, offering):
        """
        Update the document of a concrete offering in the search index
        """

        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            raise Exception('The index does not exists')

        index = open_dir(self._index_path)

        index_writer = index.writer()
        text = self._aggregate_text(offering)
        purchasers_text = self._aggregate_purchasers(offering)

        in_date = None
        if offering.state == 'uploaded':
            in_date = offering.creation_date
        else:
            in_date = offering.publication_date

        # Get the document
        index_writer.update_document(
            id=unicode(offering.pk),
            owner=unicode(offering.owner_organization.pk),
            content=unicode(text),
            name=unicode(offering.name),
            popularity=Decimal(offering.rating),
            date=in_date,
            state=unicode(offering.state),
            purchaser=purchasers_text
        )

        index_writer.commit()

    def full_text_search(self, user, text, state=None, count=False, pagination=None, sort=None):
        """
        Performs a full text search over the search index allowing for counting, filtering
        by state, paginating and sorting.
        """

        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            raise Exception('The index does not exist')

        # Get the index reader
        index = open_dir(self._index_path)

        with index.searcher() as searcher:

            # Create the query
            query_ = QueryParser('content', index.schema).parse(unicode(text))

            # If an state has been defined filter the result
            if state:
                if state == 'all':  # All user owned offerings
                    filter_ = query.Term('owner', unicode(user.userprofile.current_organization.pk))
                elif state == 'purchased':  # Purchased offerings
                    filter_ = query.Term('purchaser', user.userprofile.current_organization.pk)
                elif state == 'uploaded' or state == 'deleted':  # Uploaded or deleted offerings owned by the user
                    filter_ = query.Term('state', state) & query.Term('owner', unicode(user.userprofile.current_organization.pk))
                else:
                    raise ValueError('Invalid state')
            else:
                # If state is not included the default behaviour is returning
                # published offerings
                filter_ = query.Term('state', 'published')

            # Create sorting params if needed
            if sort:
                if sort == 'popularity' or sort == 'date':
                    reverse = True
                elif sort == 'name':
                    reverse = False
                else:
                    raise ValueError('Undefined sorting')

            # If pagination has been defined, limit the results
            if pagination:
                # Validate pagination fields
                if not isinstance(pagination, dict):
                    raise TypeError('Invalid pagination type')

                if not 'start' in pagination or not 'limit' in pagination:
                    raise ValueError('Missing required field in pagination')

                if not isinstance(pagination['start'], int) or not isinstance(pagination['limit'], int):
                    raise TypeError('Invalid pagination params type')

                if pagination['start'] < 1:
                    raise ValueError('Start param must be higher than 0')

                if pagination['limit'] < 0:
                    raise ValueError('Limit param must be positive')

                if sort:
                    search_result = searcher.search_page(query_, pagination['start'], filter=filter_, pagelen=pagination['limit'], sortedby=sort, reverse=reverse)
                else:
                    search_result = searcher.search_page(query_, pagination['start'], filter=filter_, pagelen=pagination['limit'])
            else:
                if sort:
                    search_result = searcher.search(query_, filter=filter_, limit=None, sortedby=sort, reverse=reverse)
                else:
                    search_result = searcher.search(query_, filter=filter_, limit=None)
                

            result = []
            # The get_offering_info method is imported inside this method in order to avoid a cross-reference import error
            from wstore.offerings.offerings_management import get_offering_info


            if not count:
                for hit in search_result:

                    # Get the offerings
                    offering = Offering.objects.get(pk=hit['id'])
                    result.append(get_offering_info(offering, user))
            else:
                result = {'number': len(search_result)}

        return result
