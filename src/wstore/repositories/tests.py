from django.test import TestCase

from wstore.repositories.repositories_management import register_repository, unregister_repository, get_repositories
from wstore.models import Repository


class RegisteringRepositoriesTestCase(TestCase):

    fixtures = ['reg_rep.json']

    def test_basic_registering_rep(self):

        name = 'test_repository'
        host = 'http://testrepository.com/'
        register_repository(name, host)

        rep = Repository.objects.get(name=name, host=host)
        self.assertEqual(name, rep.name)
        self.assertEqual(host, rep.host)

    def test_register_existing_repository(self):

        name = 'test_repository1'
        host = 'http://testrepository.com/'

        error = False
        msg = None

        try:
            register_repository(name, host)
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'The repository already exists')


class UnregisteringRepositoriesTestCase(TestCase):

    fixtures = ['del_rep.json']

    def test_basic_unregistering_rep(self):

        unregister_repository('test_repository')

        deleted = False
        try:
            Repository.objects.get(name='test_repository')
        except:
            deleted = True

        self.assertTrue(deleted)

    def test_unregister_not_existing_rep(self):

        error = False
        msg = None

        try:
            unregister_repository('test_repository1')
        except Exception, e:
            error = True
            msg = e.message

        self.assertTrue(error)
        self.assertEqual(msg, 'Not found')


class RepositoriesRetrievingTestCase(TestCase):

    fixtures = ['get_rep.json']

    def test_basic_retrieving_repositories(self):

        rep = get_repositories()

        self.assertEqual(rep[0]['name'], 'test_repository1')
        self.assertEqual(rep[0]['host'], 'http://testrepository1.com/')
        self.assertEqual(rep[1]['name'], 'test_repository2')
        self.assertEqual(rep[1]['host'], 'http://testrepository2.com/')
        self.assertEqual(rep[2]['name'], 'test_repository3')
        self.assertEqual(rep[2]['host'], 'http://testrepository3.com/')
