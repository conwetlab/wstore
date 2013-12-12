#!/bin/bash
# Modify $MAKE_FILE to match local environment
MAKE_FILE=Makefile
cd $WORKSPACE/src/pylucene-3.6.2-1/

sed -i '100s/#PREFIX_PYTHON=\/usr/PREFIX_PYTHON=$(WORKSPACE)\/src\/virtenv/g' $MAKE_FILE
sed -i '101s/#ANT=JAVA_HOME=\/usr\/lib\/jvm\/java-7-openjdk-amd64 \/usr\/bin\/ant/ANT=JAVA_HOME=\/usr\/lib\/jvm\/java-7-openjdk-amd64 \/usr\/bin\/ant/g' $MAKE_FILE
sed -i '102s/#PYTHON=$(PREFIX_PYTHON)\/bin\/python/PYTHON=$(PREFIX_PYTHON)\/bin\/python/g' $MAKE_FILE
sed -i '103s/#JCC=$(PYTHON) -m jcc --shared/JCC=$(PYTHON) -m jcc --shared/g' $MAKE_FILE
sed -i '104s/#NUM_FILES=4/NUM_FILES=4/g' $MAKE_FILE
