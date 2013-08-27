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

from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from django.conf import settings

class Http403(Exception):
    pass

def logout(request):

    django_logout(request)
    if settings.OILAUTH:
        url = 'https://account.lab.fi-ware.eu/users/sign_out'
    else:
        url = '/login?next=/'
    return HttpResponseRedirect(url)
