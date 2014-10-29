#!/bin/bash
set -e

# Define variables used in all scripts if not already set
if [[ -z "$WORKSPACE" ]]
  then
    export WORKSPACE=`pwd`
fi

if [[ -z "$PIP_DOWNLOAD_CACHE" ]]
  then
    export PIP_DOWNLOAD_CACHE=~/.pip_cache
fi

# Activate Virtualenv
cd $WORKSPACE/src

# Check if virtualenv is installed
set +e
hash virtualenv-2.7 &> /dev/null
VIRT27=true
if [ $? -eq 1 ]; then
    VIRT27=false
fi
set -e

if [ !$VIRT27 ]; then
    virtualenv virtenv
else
    virtualenv-2.7 virtenv
fi

source virtenv/bin/activate

$WORKSPACE/python-dep-install.sh

# Create project directories
cd $WORKSPACE/src
mkdir -p media/{bills,resources}
mkdir -p wstore/search/indexes
mkdir -p wstore/social/indexes

# Test installation
$WORKSPACE/coverage.sh

# Configure installation
if [[ "$1" != "--noinput" ]]
  then
    $WORKSPACE/configure.sh
fi
