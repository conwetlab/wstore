#!/bin/bash

export WORKSPACE=`pwd`

virtualenv-2.7 virtenv
source virtenv/bin/activate

# download Python dependencies
export PIP_DOWNLOAD_CACHE=~/.pip_cache
pip install lxml "rdflib>=3.2.0" pymongo
pip install git+https://github.com/django-nonrel/django@nonrel-1.4
pip install git+https://github.com/django-nonrel/djangotoolbox@toolbox-1.4
pip install git+https://github.com/django-nonrel/mongodb-engine@mongodb-engine-1.4-beta
pip install https://github.com/RDFLib/rdflib-jsonld/archive/master.zip

pip install git+https://github.com/conwetlab/paypalpy.git
pip install nose django-nose

# CHECK THIS DEPENDENCIES TO BE IDM-independent
pip install django-social-auth
pip install django-crontab


# download to $CACHE directory to avoid wasting bandwidth
# then extract it to the correct directory
CACHE=~/.cache
wget -N --directory-prefix=$CACHE http://apache.rediris.es/lucene/pylucene/pylucene-3.6.2-1-src.tar.gz
tar -xf $CACHE/pylucene-3.6.2-1-src.tar.gz

cd $WORKSPACE/src

mkdir media
mkdir media/bills
mkdir media/resources
mkdir wstore/search/index

