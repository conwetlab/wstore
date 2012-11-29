
import urllib2
from urllib2 import HTTPError
from urllib import urlencode
from urlparse import urljoin, urlparse

from store_commons.utils.method_request import MethodRequest


class RepositoryAdaptor():

    _repository_url = None
    _collection = None

    def __init__(self, repository_url, collection):
        self._repository_url = repository_url
        self._collection = collection

        if not self._collection.endswith('/'):
            self._collection += '/'

    def upload(self, name, content_type, data):

        url = urljoin(self._repository_url, self._collection)
        url = urljoin(url, name)
        opener = urllib2.build_opener()

        headers = {'content-type': content_type}
        request = MethodRequest('PUT', url, data, headers)

        response = opener.open(request)

        if response.code != 200:
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return url

    def download(self, name, content_type):

        url = urljoin(self._repository_url, self._collection, name)
        opener = urllib2.build_opener()

        headers = {'Accept': content_type}
        request = MethodRequest('GET', url, '', headers)

        response = opener.open(request)

        if response.code != 200:
            raise HTTPError(response.url, response.code, response.msg, None, None)

        return response.read()
