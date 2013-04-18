import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from django.utils.encoding import smart_str
from django.views.static import serve
from django.contrib.auth.models import User
from django.http import HttpResponse

from store_commons.utils.http import build_error_response
from wstore.models import UserProfile
from wstore.models import Purchase
from wstore.models import Resource
from wstore.models import Offering


@login_required
def home(request):
    return render(request, 'index.html')


@login_required
def admin(request):
    if request.user.is_staff:
        return render(request, 'admin/admin.html')
    else:
        build_error_response(request, 401, 'Unathorized')


@login_required
def catalogue(request):
    profile = UserProfile.objects.get(user=request.user)
    context = {'roles': profile.roles}
    return render(request, 'catalogue/catalogue.html', context)


@login_required
def serve_media(request, path, name):
    if request.method != 'GET':
        return build_error_response(request, 415, 'Method not supported')

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
            for off in user_profile.organization.offerings_purchased:
                o = Offering.objects.get(pk=off)

                for res in o.resources:
                    if str(res) == resource.pk:
                        found = True
                        break

                if found:
                    break

            if not found:
                return build_error_response(request, 404, 'Not found')

    if dir_path.endswith('bills'):
        user_profile = UserProfile.objects.get(user=request.user)
        purchase = Purchase.objects.get(ref=name[:-15])

        if purchase.organization_owned:
            user_org = user_profile.organization
            if not purchase.owner_organization == user_org.name:
                return build_error_response(request, 404, 'Not found')
        else:
            if not purchase.customer == request.user:
                return build_error_response(request, 404, 'Not found')

    local_path = os.path.join(dir_path, name)

    if not os.path.isfile(local_path):
        return build_error_response(request, 404, 'Not found')

    if not getattr(settings, 'USE_XSENDFILE', False):
        return serve(request, local_path, document_root='/')
    else:
        response = HttpResponse()
        response['X-Sendfile'] = smart_str(local_path)
        return response
