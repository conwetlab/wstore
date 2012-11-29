import json
from lxml import etree
from urllib2 import HTTPError

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.sites.models import get_current_site
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from store_commons.resource import Resource
from store_commons.utils.http import build_error_response, get_content_type, supported_request_mime_types
from fiware_store.models import Marketplace
from market_adaptor.marketadaptor import MarketAdaptor


class MarketplaceCollection(Resource):

    # Creates a new marketplace resource, that is
    # register the store in a marketplace and
    # add the marketplace info needed for access in
    # the database
    @method_decorator(login_required)
    @supported_request_mime_types(('application/json', 'application/xml'))
    def create(self, request):

        if not request.user.is_staff:  # Only an admin could register the store in a marketplace
            return build_error_response(request, 401, 'Unautorized')

        store_name = settings.STORE_NAME
        content_type = get_content_type(request)[0]

        name = None
        host = None
        # Content types json and xml are supported
        if content_type == 'application/json':

            try:
                content = json.loads(request.raw_post_data)
                name = content['name']
                host = content['host']
            except:
                msg = "Request body is not valid JSON data"
                return build_error_response(request, 400, msg)

        else:

            try:
                content = etree.fromstring(request.raw_post_data)
                name = content.xpath('/marketplace/name')[0].text
                host = content.xpath('/marketplace/host')[0].text
            except:
                msg = "Request body is not a valid XML data"
                return build_error_response(request, 400, msg)

        if host[-1] != '/':
            host += '/'

        marketadaptor = MarketAdaptor(host)
        store_info = {
            'store_name': store_name,
            'store_uri': 'http://' + get_current_site(request).domain,
        }
        try:
            marketadaptor.add_store(store_info)
        except HTTPError, e:
            return build_error_response(request, 502, 'Bad gateway')

        # Only if the store has been registered, the marketplace resource is created
        Marketplace.objects.create(name=name, host=host)

        return build_error_response(request, 201, 'Created')

    @method_decorator(login_required)
    def read(self, request):

        # Read Accept header to know the response mime type, JSON by default
        accept = request.META.get('ACCEPT', '')
        marketplaces = Marketplace.objects.all()
        response = None
        mime_type = None

        if accept == '' or accept.find('application/JSON') > -1:
            response = []

            for market in marketplaces:
                response.append({
                    'name': market.name,
                    'host': market.host
                })

            response = json.dumps(response)
            mime_type = 'application/JSON; charset=UTF-8'

        elif accept.find('application/xml') > -1:
            root_elem = etree.Element('Marketplaces')

            for market in marketplaces:
                market_elem = etree.SubElement(root_elem, 'Marketplace')
                name_elem = etree.SubElement(market_elem, 'Name')
                name_elem.text = market.name
                host_elem = etree.SubElement(market_elem, 'Host')
                host_elem.text = market.host

            response = etree.tounicode(root_elem)
            mime_type = 'application/xml; charset=UTF-8'

        else:
            return build_error_response(request, 400, 'Invalid requested type')

        return HttpResponse(response, status=200, mimetype=mime_type)


class MarketplaceEntry(Resource):

    @method_decorator(login_required)
    def read(self, request, market):
        pass

    @method_decorator(login_required)
    def update(self, request, market):
        pass

    @method_decorator(login_required)
    def delete(self, request, market):

        if not request.user.is_staff:
            return build_error_response(request, 401, 'Unathorized')

        marketplace = None
        try:
            marketplace = Marketplace.objects.get(name=market)
        except:
            return build_error_response(request, 404, 'Not found')

        host = marketplace.host
        if host[-1] != '/':
            host += '/'

        marketadaptor = MarketAdaptor(host)

        try:
            marketadaptor.delete_store(settings.STORE_NAME)
        except HTTPError, e:
            return build_error_response(request, 502, 'Bad gateway')

        marketplace.delete()
        return build_error_response(request, 204, 'No content')
