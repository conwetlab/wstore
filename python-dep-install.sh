#!/bin/bash
# Download and install Python dependencies
pip install lxml "rdflib>=3.2.0" pymongo
pip install git+https://github.com/django-nonrel/django@nonrel-1.4
pip install git+https://github.com/django-nonrel/djangotoolbox@toolbox-1.4
pip install git+https://github.com/django-nonrel/mongodb-engine@mongodb-engine-1.4-beta
pip install https://github.com/RDFLib/rdflib-jsonld/archive/master.zip

pip install git+https://github.com/conwetlab/paypalpy.git
pip install nose django-nose

pip install django-social-auth
pip install django-crontab
