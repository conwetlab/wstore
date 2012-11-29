
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
