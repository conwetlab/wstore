import os
import json
import lucene
import rdflib
from lucene import SimpleFSDirectory, File, Document, Field, \
StandardAnalyzer, IndexWriter, Version, IndexSearcher, QueryParser

from fiware_store.offerings.offerings_management import get_offering_info
from fiware_store.models import Offering


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
        lucene.initVM()

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

    def full_text_search(self, user, text, state=None):

        if not os.path.exists(self._index_path) or os.listdir(self._index_path) == []:
            raise Exception('The index not exist')

        # Get the index reader
        lucene.initVM()
        index = SimpleFSDirectory(File(self._index_path))
        analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        lucene_searcher = IndexSearcher(index)

        # perform the query
        query = QueryParser(Version.LUCENE_CURRENT, 'content', analyzer).parse(text)

        max_number = 1000
        total_hits = lucene_searcher.search(query, max_number)

        result = []

        for hit in total_hits.scoreDocs:
            doc = lucene_searcher.doc(hit.doc)

            # Get the offerings
            offering = Offering.objects.get(pk=doc.get('id'))
            offering_info = get_offering_info(offering, user)

            # filter the offerings
            # if no state provided means that all published offerings are wanted
            if state == None:
                if offering_info['state'] == 'published' or offering_info['state'] == 'purchased':
                    result.append(offering_info)

            elif state == 'purchased':
                if offering_info['state'] == 'purchased':
                    result.append(offering_info)

            elif state == 'all':
                if offering.owner_admin_user == user:
                    result.append(offering_info)
            else:
                if offering.owner_admin_user == user and offering_info['state'] == state:
                    result.append(offering_info)

        return result
