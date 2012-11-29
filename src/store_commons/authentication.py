from django.contrib.auth import logout as django_logout
from django.shortcuts import render

class Http403(Exception):
    pass

def logout(request, template='registration/logout.html'):

    django_logout(request)
    return render(request, template)
