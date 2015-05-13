import os
import sys
import site

site.addsitedir('/home/francisco/store_env-1.4/local/lib/python2.7/site-packages')

path = '/home/francisco/Trabajo/WStore/src'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Activate your virtual env
activate_env=os.path.expanduser("/home/francisco/store_env-1.4/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()