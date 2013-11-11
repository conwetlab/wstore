#!/bin/bash
# Download to $CACHE directory to avoid wasting bandwidth
# then extract it to the correct directory
CACHE=~/.cache
wget -N --directory-prefix=$CACHE http://apache.rediris.es/lucene/pylucene/pylucene-3.6.2-1-src.tar.gz
tar -xf $CACHE/pylucene-3.6.2-1-src.tar.gz

# Building up PyLucene bindings
cd $WORKSPACE/src/pylucene-3.6.2-1/jcc
python setup.py build
python setup.py install

$WORKSPACE/pylucene-patch-make-env.sh

cd $WORKSPACE/src/pylucene-3.6.2-1

# Compile and install PyLucene
make
make install
