import os
import lucene
from lucene import SimpleFSDirectory, File, Document, Field, \
StandardAnalyzer, IndexWriter, Version, IndexSearcher, QueryParser

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from wstore.search.search_engine import SearchEngine
from wstore.models import UserProfile
from wstore.models import Organization
from wstore.models import Offering


class FakeUSDLParser():

    def __init__(self, data, type_):
        pass

    def parse(self):
        return {
            'pricing': {
                'price_plans': [{
                    'price_components': []
                }]
            }
        }


class IndexCreationTestCase(TestCase):

    fixtures = ['create_index.json']

    @classmethod
    def tearDownClass(cls):
        path = settings.BASEDIR + '/wstore/test/test_index'
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            os.remove(file_path)

        os.rmdir(path)

    def test_basic_index_creaton(self):

        offering = Offering.objects.get(name='test_offering')
        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        se.create_index(offering)

        lucene.initVM()
        index = SimpleFSDirectory(File(settings.BASEDIR + '/wstore/test/test_index'))
        analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        lucene_searcher = IndexSearcher(index)
        query = QueryParser(Version.LUCENE_CURRENT, 'content', analyzer).parse('widget')

        max_number = 1000
        total_hits = lucene_searcher.search(query, max_number)

        self.assertEqual(len(total_hits.scoreDocs), 1)
        doc = lucene_searcher.doc(total_hits.scoreDocs[0].doc)
        self.assertEqual(offering.pk, doc.get('id'))


class FullTextSearchTestCase(TestCase):

    fixtures = ['full_text.json']

    @classmethod
    def setUpClass(cls):
        # Create the test index
        lucene.initVM()
        index_path = settings.BASEDIR + '/wstore/test/test_index'
        index = SimpleFSDirectory(File(index_path))
        analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        index_writer = IndexWriter(index, analyzer, True, IndexWriter.MaxFieldLength.UNLIMITED)
        # Add documents  to the index
        document = Document()
        text1 = 'first test index offering'
        document.add(Field("content", text1, Field.Store.YES, Field.Index.ANALYZED))
        document.add(Field("id", "61000aba8e05ac2115f022f9", Field.Store.YES, Field.Index.NOT_ANALYZED))
        index_writer.addDocument(document)

        text2 = 'second test index offering'
        document = Document()
        document.add(Field("content", text2, Field.Store.YES, Field.Index.ANALYZED))
        document.add(Field("id", "61000aba8e05ac2115f022ff", Field.Store.YES, Field.Index.NOT_ANALYZED))
        index_writer.addDocument(document)
        document = Document()
        document.add(Field("content", "uploaded", Field.Store.YES, Field.Index.ANALYZED))
        document.add(Field("id", "61000aba8e05ac2115f022f0", Field.Store.YES, Field.Index.NOT_ANALYZED))

        index_writer.addDocument(document)

        document = Document()
        document.add(Field("content", "purchased", Field.Store.YES, Field.Index.ANALYZED))
        document.add(Field("id", "61000a0a8905ac2115f022f0", Field.Store.YES, Field.Index.NOT_ANALYZED))
        index_writer.addDocument(document)
        index_writer.optimize()
        index_writer.close()

        from wstore.offerings import offerings_management
        offerings_management.USDLParser = FakeUSDLParser

        super(FullTextSearchTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        path = settings.BASEDIR + '/wstore/test/test_index'
        files = os.listdir(path)
        for f in files:
            file_path = os.path.join(path, f)
            os.remove(file_path)

        os.rmdir(path)

    def test_basic_search(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'first')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test_offering1')
        self.assertEqual(result[0]['version'], '1.0')

    def test_search_multiple_results(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'index offering')

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'test_offering1')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[1]['name'], 'test_offering2')
        self.assertEqual(result[1]['version'], '1.0')

    def test_search_no_results(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'no result')

        self.assertEqual(len(result), 0)

    def test_search_for_uploaded_offerings(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'uploaded', state='uploaded')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'uploaded_offering')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[0]['state'], 'uploaded')

    def test_search_for_purchased_offerings(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.offerings_purchased = ["61000a0a8905ac2115f022f0"]
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/test_index')
        result = se.full_text_search(user, 'purchased', state='purchased')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'purchased_offering')
        self.assertEqual(result[0]['version'], '1.0')
        self.assertEqual(result[0]['state'], 'purchased')

    def test_search_not_existing_index(self):
        user = User.objects.get(username='test_user')
        user_profile = UserProfile.objects.get(user=user)

        org = Organization.objects.get(name='test_organization')
        user_profile.organization = org
        user_profile.save()

        se = SearchEngine(settings.BASEDIR + '/wstore/test/no_index')

        error = False
        msg = None
        try:
            se.full_text_search(user, 'index offering')
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'The index not exist')
