# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

import json
import urllib2
import threading
from bson import ObjectId
from lxml import etree
from urllib2 import HTTPError
from urlparse import urljoin

from wstore.store_commons.utils.method_request import MethodRequest
from wstore.store_commons.database import get_database_connection
from wstore.models import Organization


class RSSAdaptorThread(threading.Thread):

    def __init__(self, rss, cdr_info):
        threading.Thread.__init__(self)
        self.rss = rss
        self.cdr = cdr_info

    def run(self):
        from wstore.rss_adaptor.rss_manager_factory import RSSManagerFactory
        rss_factory = RSSManagerFactory(self.rss)
        r = rss_factory.get_rss_adaptor()
        r.send_cdr(self.cdr)


class RSSAdaptor():
    _rss = None

    def __init__(self, rss):
        self._rss = rss


class RSSAdaptorV1(RSSAdaptor):

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

        rss_url = self._rss.host
        opener = urllib2.build_opener()

        if not rss_url.endswith('/'):
            rss_url += '/'

        url = urljoin(rss_url, 'fiware-rss/rss/cdrs')
        data = etree.tostring(root, pretty_print=True, xml_declaration=True)

        headers = {
            'content-type': 'application/xml',
            'X-Auth-Token': self._rss.access_token
        }
        request = MethodRequest('POST', url, data, headers)

        response = opener.open(request)

        if not (response.code > 199 and response.code < 300):
            raise HTTPError(response.url, response.code, response.msg, None, None)


class RSSAdaptorV2(RSSAdaptor):

    def send_cdr(self, cdr_info):

        # Build CDRs
        data = []
        for cdr in cdr_info:
            time = cdr['time_stamp'].split(' ')
            time = time[0] + 'T' + time[1] + 'Z'

            data.append({
                'cdrSource': self._rss.aggregator_id,
                'productClass': cdr['product_class'],
                'correlationNumber': cdr['correlation'],
                'timestamp': time,
                'application': cdr['offering'],
                'transactionType': 'C',
                'event': cdr['event'],
                'referenceCode': cdr['purchase'],
                'description': cdr['description'],
                'chargedAmount': cdr['cost_value'],
                'chargedTaxAmount': cdr['tax_value'],
                'currency': cdr['cost_currency'],
                'customerId': cdr['customer'],
                'appProvider': cdr['provider']
            })

        # Make request
        url = urljoin(self._rss.host, 'fiware-rss/rss/cdrs')
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + self._rss.access_token
        }

        request = MethodRequest('POST', url, json.dumps(data), headers)

        opener = urllib2.build_opener()
        try:
            try:
                opener.open(request)
            except HTTPError as e:
                if e.code == 401:
                    self._rss.refresh_token()
                    headers['Authorization'] = 'Bearer ' + self._rss.access_token
                    request = MethodRequest('POST', url, json.dumps(data), headers)
                    opener.open(request)
                else:
                    raise e
        except:

            db = get_database_connection()
            # Restore correlation numbers
            for cdr in cdr_info:
                org = Organization.objects.get(actor_id=cdr['provider'])
                db.wstore_organization.find_and_modify(
                    query={'_id': ObjectId(org.pk)},
                    update={'$inc': {'correlation_number': -1}}
                )['correlation_number']
