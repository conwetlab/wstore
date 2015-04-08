#!/bin/bash
# Download and install Python dependencies
pip install lxml "rdflib>=3.2.0" "pymongo==2.8"
pip install https://github.com/django-nonrel/django/archive/nonrel-1.4.zip
pip install https://github.com/django-nonrel/djangotoolbox/archive/toolbox-1.4.zip
pip install https://github.com/django-nonrel/mongodb-engine/archive/mongodb-engine-1.4-beta.zip
pip install https://github.com/RDFLib/rdflib-jsonld/archive/master.zip

pip install https://github.com/conwetlab/paypalpy/archive/master.zip
pip install nose django-nose

pip install django-social-auth
pip install django-crontab
pip install Whoosh
pip install Stemming
pip install requests
