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

import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from django.utils.encoding import smart_str
from django.views.static import serve
from django.contrib.auth.models import User
from django.http import HttpResponse

from store_commons.utils.http import build_response
from wstore.store_commons.resource import Resource as API_Resource
from wstore.models import UserProfile
from wstore.models import Purchase
from wstore.models import Resource
from wstore.models import Offering


@login_required
def home(request):
    return render(request, 'index.html', {
        'organization': request.user.userprofile.current_organization.name})


@login_required
def admin(request):
    if request.user.is_staff:
        return render(request, 'admin/admin.html')
    else:
        build_response(request, 403, 'Forbidden')


@login_required
def catalogue(request):
    profile = UserProfile.objects.get(user=request.user)
    context = {
        'roles': profile.get_current_roles(),
        'usdl_editor': settings.USDL_EDITOR_URL,
	'organization': profile.current_organization.name
    }
    return render(request, 'catalogue/catalogue.html', context)


class ServeMedia(API_Resource):

    def read(self, request, path, name):
        if request.method != 'GET':
            return build_response(request, 415, 'Method not supported')

        dir_path = os.path.join(settings.MEDIA_ROOT, path)

        # Protect the resources from not authorized downloads
        if dir_path.endswith('resources'):
            user_profile = UserProfile.objects.get(user=request.user)
            found = False

            # Check if the request user has access to the resource
            splited_name = name.split('__')
            prov = User.objects.get(username=splited_name[0])
            resource = Resource.objects.get(provider=prov, name=splited_name[1], version=splited_name[2])

            # Check if the user has purchased an offering with the resource
            for off in user_profile.offerings_purchased:
                o = Offering.objects.get(pk=off)

                for res in o.resources:
                    if str(res) == resource.pk:
                        found = True
                        break

                if found:
                    break

            if not found:
                # Check if the user organization has an offering with the resource
                for off in user_profile.current_organization.offerings_purchased:
                    o = Offering.objects.get(pk=off)

                    for res in o.resources:
                        if str(res) == resource.pk:
                            found = True
                            break

                    if found:
                        break

                if not found:
                    return build_response(request, 404, 'Not found')

        if dir_path.endswith('bills'):
            user_profile = UserProfile.objects.get(user=request.user)
            purchase = Purchase.objects.get(ref=name[:24])

            if purchase.organization_owned:
                user_org = user_profile.current_organization
                if not purchase.owner_organization.name == user_org.name:
                    return build_response(request, 404, 'Not found')
            else:
                if not purchase.customer == request.user:
                    return build_response(request, 404, 'Not found')

        local_path = os.path.join(dir_path, name)

        if not os.path.isfile(local_path):
            return build_response(request, 404, 'Not found')

        if not getattr(settings, 'USE_XSENDFILE', False):
            return serve(request, local_path, document_root='/')
        else:
            response = HttpResponse()
            response['X-Sendfile'] = smart_str(local_path)
            return response
