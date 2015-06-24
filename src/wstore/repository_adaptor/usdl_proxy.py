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

from django.http import HttpResponse

from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_response
from wstore.repository_adaptor.repositoryAdaptor import unreg_repository_adaptor_factory
from wstore.models import Offering, Organization


class USDLCollection(Resource):

    def read(self, request, organization, name, version):
        # Get offering
        try:
            org = Organization.objects.get(name=organization)
            offering = Offering.objects.get(owner_organization=org, name=name, version=version)
        except:
            return build_response(request, 404, 'Not found')

        # Get usdl from repository
        try:
            adaptor = unreg_repository_adaptor_factory(offering.description_url)
            result = adaptor.download()
        except:
            return build_response(request, 502, 'Bad Gateway')

        # Return the USDL with the origin format
        return HttpResponse(result['data'], status=200, mimetype=result['content_type'])
