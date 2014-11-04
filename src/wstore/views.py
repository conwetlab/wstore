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
import json
import smtplib

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from django.utils.encoding import smart_str
from django.views.static import serve
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from store_commons.utils.http import build_response, authentication_required, \
supported_request_mime_types
from wstore.store_commons.resource import Resource as API_Resource
from wstore.models import UserProfile, Organization
from wstore.models import Purchase, Resource, Offering
from wstore.offerings.offerings_management import get_offering_info


MAIN_PORTAL_URL = "http://help.lab.fi-ware.org/"
CLOUD_PORTAL_URL = "http://cloud.lab.fi-ware.org/"
MASHUP_PORTAL_URL = "http://mashup.lab.fi-ware.org/"
ACCOUNT_PORTAL_URL = "https://account.lab.fi-ware.org/"
DATA_PORTAL_URL = "https://data.lab.fi-ware.org/"

def _load_home_context(request):
    context = {
       'organization': request.user.userprofile.current_organization.name,
       'oil': settings.OILAUTH,
       'portal': settings.PORTALINSTANCE
    }
    # Include Portals URLs if needed
    if settings.PORTALINSTANCE:
        context['main'] = MAIN_PORTAL_URL
        context['cloud'] = CLOUD_PORTAL_URL
        context['mashup'] = MASHUP_PORTAL_URL
        context['account'] = ACCOUNT_PORTAL_URL
        context['data'] = DATA_PORTAL_URL

    return context


@login_required
def home(request):
    context = _load_home_context(request)
    context['loader'] = 'home'
    return render(request, 'index.html', context)


@login_required
def home_search(request):
    context = _load_home_context(request)

    context['loader'] = 'offerings'
    return render(request, 'index.html', context)


@login_required
def home_search_text(request, keyword):
    context = _load_home_context(request)

    context['loader'] = 'keyword'
    context['info'] = mark_safe(keyword)
    return render(request, 'index.html', context)


@login_required
def home_search_tag(request, tag):
    context = _load_home_context(request)

    context['loader'] = 'tag'
    context['info'] = tag
    return render(request, 'index.html', context)


@login_required
def home_details(request, org, name, version):
    context = _load_home_context(request)

    context['loader'] = 'details'
    try:
        owner_org = Organization.objects.get(name=org)
        offering = Offering.objects.get(owner_organization=owner_org, name=name, version=version)
        offering_info = get_offering_info(offering, request.user)
    except:
        return build_response(request, 404, 'Not found')

    context['info'] = mark_safe(json.dumps(offering_info))
    return render(request, 'index.html', context)


@login_required
def home_search_resource(request, org, name, version):
    context = _load_home_context(request)

    context['loader'] = 'resource'
    context['info'] = mark_safe(json.dumps({
        'org': org,
        'name': name,
        'version': version
    }))

    return render(request, 'index.html', context)


@login_required
def admin(request):
    if request.user.is_staff:
        context = {
            'oil': settings.OILAUTH,
            'portal': settings.PORTALINSTANCE
        }

        # Include Portals URLs if needed
        if settings.PORTALINSTANCE:
            context['main'] = MAIN_PORTAL_URL
            context['cloud'] = CLOUD_PORTAL_URL
            context['mashup'] = MASHUP_PORTAL_URL
            context['account'] = ACCOUNT_PORTAL_URL
            context['data'] = DATA_PORTAL_URL

        return render(request, 'admin/admin.html', context)
    else:
        return build_response(request, 403, 'Forbidden')


@login_required
def catalogue(request):

    profile = UserProfile.objects.get(user=request.user)
    context = {
        'roles': profile.get_current_roles(),
        'usdl_editor': settings.USDL_EDITOR_URL,
	    'organization': profile.current_organization.name,
        'oil': settings.OILAUTH,
        'portal': settings.PORTALINSTANCE
    }
    # Include Portals URLs if needed
    if settings.PORTALINSTANCE:
        context['main'] = MAIN_PORTAL_URL
        context['cloud'] = CLOUD_PORTAL_URL
        context['mashup'] = MASHUP_PORTAL_URL
        context['account'] = ACCOUNT_PORTAL_URL
        context['data'] = DATA_PORTAL_URL

    return render(request, 'catalogue/catalogue.html', context)

@login_required
def organization(request):

    if not settings.OILAUTH:
        profile = UserProfile.objects.get(user=request.user)
        context = {
            'roles': profile.get_current_roles(),
	        'organization': profile.current_organization.name,
            'oil': settings.OILAUTH,
            'portal': settings.PORTALINSTANCE
        }
        # Include Portals URLs if needed
        if settings.PORTALINSTANCE:
            context['main'] = MAIN_PORTAL_URL
            context['cloud'] = CLOUD_PORTAL_URL
            context['mashup'] = MASHUP_PORTAL_URL
            context['account'] = ACCOUNT_PORTAL_URL
            context['data'] = DATA_PORTAL_URL

        return render(request, 'organizations/organization_template.html', context)
    else:
        return build_response(request, 403, 'This view is not enabled with iDM auth')


class ProviderRequest(API_Resource):

    @authentication_required
    @supported_request_mime_types(('application/json',))
    def create(self, request):

        # Get user info
        try:
            data = json.loads(request.raw_post_data)
            if not 'username' in data or not 'message' in data:
                raise Exception('')
        except:
            return build_response(request, 400, 'Invalid Json content')

        try:
            user = User.objects.get(username=data['username'])
        except:
            return build_response(request, 400, 'Invalid user')

        try:
            # Send email
            fromaddr = settings.WSTOREMAIL
            toaddrs = settings.WSTOREPROVIDERREQUEST
            msg = 'Subject: Provider request: ' + user.username + '\n'
            msg += user.userprofile.complete_name + '\n'
            msg += data['message']

            # Credentials (if needed)
            username = settings.WSTOREMAILUSER
            password = settings.WSTOREMAILPASS

            # The mail is sent
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(username, password)
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
        except:
            return build_response(request, 400, 'Problem sending the email')

        user.userprofile.provider_requested = True

        user.userprofile.save()

        return build_response(request, 200, 'OK')


class ServeMedia(API_Resource):

    def read(self, request, path, name):
        if request.method != 'GET':
            return build_response(request, 415, 'Method not supported')

        dir_path = os.path.join(settings.MEDIA_ROOT, path)

        # Protect the resources from not authorized downloads
        if dir_path.endswith('resources') :

            # Check if the request user has access to the resource
            splited_name = name.split('__')
            prov = Organization.objects.get(name=splited_name[0])
            resource = Resource.objects.get(provider=prov, name=splited_name[1], version=splited_name[2])

            if not resource.open:
                user_profile = UserProfile.objects.get(user=request.user)
                found = False

                # Check if the user has purchased an offering with the resource 
                # only if the offering is not open
            
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
