from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect

class Http403(Exception):
    pass

def logout(request):

    django_logout(request)
    return HttpResponseRedirect('/login?next=/')
