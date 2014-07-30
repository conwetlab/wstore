#!/bin/bash
pip install coverage
pip install mock
pip install nose-parameterized
pip install selenium

cd $WORKSPACE/src

coverage run --branch --source=wstore ./manage.py test --noinput --with-xunit --nologcapture -v 2
coverage xml --omit="*urls*"

# Prettify Coverate Report
COVERAGE_FILE=coverage.xml
sed -i 's/\(<coverage [^>]*>\)/\1<sources><source>src<\/source><\/sources>/' $COVERAGE_FILE
sed -i 's/\/opt\/jenkins\/jobs\/WStore-python2.6-django1.4\/workspace\/src\/virtenv\/lib\/python2.7\/site-packages\///g' $COVERAGE_FILE
sed -i 's/.opt.jenkins.jobs.WStore-python2.6-django1.4.workspace.src.virtenv.lib.python2/WStore/g' $COVERAGE_FILE
