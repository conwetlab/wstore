
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def usdl_editor(request):
    return render(request, 'usdleditor.html')
