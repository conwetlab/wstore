FROM python:2

RUN apt-get update && apt-get install -y mongodb python-pip git wkhtmltopdf xvfb gcc libxml2-dev libxslt1-dev zlib1g-dev python-dev

RUN git clone https://github.com/conwetlab/wstore.git

# Use the git folder as default folder
WORKDIR wstore

# Create required folders
RUN mkdir ./src/media
RUN mkdir ./src/media/resources
RUN mkdir ./src/media/bills
RUN mkdir ./src/wstore/search/indexes
RUN mkdir ./src/wstore/social/indexes
RUN mkdir ./src/wstore/admin/indexes

# Install basic dependencies
RUN ./python-dep-install.sh

RUN \
    service mongodb start && \
    sleep 60 && \
    ./src/manage.py createsite Local http://localhost:8000 && \
    SITE_ID=`./src/manage.py tellsiteid | grep 'SITE_ID=' | sed "s/.*'\(.*\)'.*/\1/"` && \
    sed -i "s/SITE_ID=u''/SITE_ID=u'${SITE_ID}'/g" ./src/settings.py && \
    sed -i "s/OILAUTH = True/OILAUTH = False/g" ./src/settings.py && \
    ./src/manage.py collectstatic --noinput && \
    ./src/manage.py syncdb --noinput && \
    ./src/manage.py createuser admin admin --staff

# Create volumes
VOLUME /data/db
VOLUME ./src/media
VOLUME ./src/wstore/search/indexes
VOLUME ./src/wstore/social/indexes
VOLUME ./src/wstore/admin/indexes

# WMarket will run in port 8000
EXPOSE 8000

CMD service mongodb start && \
    echo "Waiting till database is initialized" && \
    sleep 20 && \
    echo "Starting WStore" && \
    ./src/manage.py runserver 0.0.0.0:8000
