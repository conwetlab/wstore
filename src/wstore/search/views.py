import os
import json

from django.http import HttpResponse
from django.conf import settings

from wstore.store_commons.utils.http import build_error_response, authentication_required
from wstore.store_commons.resource import Resource
from wstore.search.search_engine import SearchEngine


class SearchEntry(Resource):

    @authentication_required
    def read(self, request, text):

        index_path = os.path.join(settings.BASEDIR, 'wstore')
        index_path = os.path.join(index_path, 'search')
        index_path = os.path.join(index_path, 'indexes')

        search_engine = SearchEngine(index_path)

        filter_ = request.GET.get('filter', None)

        # Check the filter value
        if filter_ and filter_ != 'published' and filter_ != 'provided' and filter_ != 'purchased':
            return build_error_response(request, 400, 'Invalid filter')

        if not filter_:
            response = search_engine.full_text_search(request.user, text)

        elif filter_ == 'provided':

            state = request.GET.get('state', 'all')
            # Check the state value
            if state != 'all' and state != 'uploaded'\
            and state != 'published' and state != 'deleted':

                return build_error_response(request, 400, 'Invalid state')

            response = search_engine.full_text_search(request.user, text, state=state)

        elif filter_ == 'purchased':
            response = search_engine.full_text_search(request.user, text, state='purchased')

        return HttpResponse(json.dumps(response), status=200, mimetype='application/json')
