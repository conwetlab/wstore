
import urllib2
from lxml import etree
from urllib2 import HTTPError
from urlparse import urljoin

from wstore.store_commons.utils.method_request import MethodRequest


class RSSAdaptor():

    _rss_url = None

    def __init__(self, rss_url):

        self._rss_url = rss_url

        if not rss_url.endswith('/'):
            self._rss_url += '/'

    def send_cdr(self, cdr_info):

        # Build XML document
        root = etree.Element('cdrs')

        for cdr in cdr_info:
            node = etree.Element('cdr')

            id_serv = etree.Element('id_service_provider')
            id_serv.text = cdr['provider']
            node.append(id_serv)

            id_app = etree.Element('id_application')
            id_app.text = cdr['service']
            node.append(id_app)

            id_evnt = etree.Element('id_event')
            id_evnt.text = cdr['defined_model']
            node.append(id_evnt)

            id_corr = etree.Element('id_correlation')
            id_corr.text = cdr['correlation']
            node.append(id_corr)

            purch_code = etree.Element('purchase_code')
            purch_code.text = cdr['purchase']
            node.append(purch_code)

            par_app_id = etree.Element('parent_app_id')
            par_app_id.text = cdr['offering']
            node.append(par_app_id)

            prod_class = etree.Element('product_class')
            prod_class.text = cdr['product_class']
            node.append(prod_class)

            desc = etree.Element('description')
            desc.text = cdr['description']
            node.append(desc)

            cost_curr = etree.Element('cost_currency')
            cost_curr.text = cdr['cost_currency']
            node.append(cost_curr)

            cost_units = etree.Element('cost_units')
            cost_units.text = cdr['cost_value']
            node.append(cost_units)

            tax_curr = etree.Element('tax_currency')
            tax_curr.text = cdr['tax_currency']
            node.append(tax_curr)

            tax_units = etree.Element('tax_units')
            tax_units.text = cdr['tax_value']
            node.append(tax_units)

            source = etree.Element('cdr_source')
            source.text = cdr['source']
            node.append(source)

            id_op = etree.Element('id_operator')
            id_op.text = cdr['operator']
            node.append(id_op)

            id_country = etree.Element('id_country')
            id_country.text = cdr['country']
            node.append(id_country)

            time_stamp = etree.Element('time_stamp')
            time_stamp.text = cdr['time_stamp']
            node.append(time_stamp)

            id_user = etree.Element('id_user')
            id_user.text = cdr['customer']
            node.append(id_user)

            root.append(node)

        opener = urllib2.build_opener()

        url = urljoin(self._rss_url, 'rss/cdrs')
        data = etree.tostring(root, pretty_print=True, xml_declaration=True)

        headers = {'content-type': 'application/xml'}
        request = MethodRequest('POST', url, data, headers)

        response = opener.open(request)

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)
