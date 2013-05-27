# -*- coding: utf-8 -*-


from urlparse import parse_qs, urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils import simplejson, unittest
from django.utils.http import urlencode


@unittest.skipIf(not 'wstore.oauth2provider' in settings.INSTALLED_APPS, 'OAuth2 provider not enabled')
class Oauth2TestCase(TestCase):

    fixtures = ('selenium_test_data', 'oauth2_test_data')
    tags = ('oauth2',)

    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        cls.user_client = Client()

    def setUp(self):
        self.user_client.login(username='normuser', password='admin')

    def test_authorization_code_grant_flow(self):

        # Authorization request
        query = {
            'response_type': 'code',
            'client_id': '3faf0fb4c2fe76c1c3bb7d09c21b97c2',
            'redirect_uri': 'https://customapp.com/oauth/redirect',
        }
        auth_req_url = reverse('oauth2provider.auth') + '?' + urlencode(query)
        response = self.user_client.get(auth_req_url)

        # Parse returned code
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('https://customapp.com/oauth/redirect'))
        response_data = parse_qs(urlparse(response['Location']).query)
        code = response_data['code'][0]

        # Access token request
        url = reverse('oauth2provider.token')
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': '3faf0fb4c2fe76c1c3bb7d09c21b97c2',
            'client_secret': '9643b7c3f59ef531931d39a3e19bcdd7',
            'redirect_uri': 'https://customapp.com/oauth/redirect',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        response_data = simplejson.loads(response.content)
        token = response_data['access_token']
        token_type = response_data['token_type']
        self.assertEqual(token_type, 'Bearer')

        # Make an authenticated request
        url = reverse('wirecloud.workspace_collection')

        response = self.client.get(url, HTTP_ACCEPT='application/json', HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(response.status_code, 200)

        response_data = simplejson.loads(response.content)
        self.assertTrue(isinstance(response_data, list))
        self.assertTrue(isinstance(response_data[0], dict))
    test_authorization_code_grant_flow.tags = ('fiware-ut-9',)

    @unittest.skip('wip test')
    def test_implicit_grant_flow(self):

        # Authorization request
        query = {
            'response_type': 'token',
            'client_id': '3faf0fb4c2fe76c1c3bb7d09c21b97c2',
            'redirect_uri': 'https://customapp.com/oauth/redirect',
        }
        auth_req_url = reverse('oauth2provider.auth') + '?' + urlencode(query)
        response = self.user_client.get(auth_req_url)

        # Parse returned code
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('https://customapp.com/oauth/redirect'))
        response_data = parse_qs(urlparse(response['Location']).query)
        token = response_data['access_token'][0]
        token_type = response_data['token_type'][0]
        self.assertEqual(token_type, 'Bearer')

        # Make an authenticated request
        url = reverse('wirecloud.workspace_collection')

        response = self.client.get(url, HTTP_ACCEPT='application/json', HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(response.status_code, 200)

        response_data = simplejson.loads(response.content)
        self.assertTrue(isinstance(response_data, list))
        self.assertTrue(isinstance(response_data[0], dict))