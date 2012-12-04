import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from django.utils.encoding import smart_str
from django.views.static import serve

from store_commons.utils.http import build_error_response
from fiware_store.models import UserProfile
import base64
import json


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
        return HttpResponseNotAllowed(('GET',))

    dir_path = os.path.join(settings.MEDIA_ROOT, path)
    local_path = os.path.join(dir_path, name)

    if not os.path.isfile(local_path):
        return HttpResponse(status=404)

    if not getattr(settings, 'USE_XSENDFILE', False):
        return serve(request, local_path, document_root='/')
    else:
        response = HttpResponse()
        response['X-Sendfile'] = smart_str(local_path)
        return response
