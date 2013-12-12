README
======

Requirements
------------

In order to have WStore up and running the following software is required

* A Web Server (i.e Apache)
* MongoDB
* Python 2.5, 2.6 or 2.7. Python 3 and other versions are not supported. 
* Django nonrel 1.3 or 1.4
* djangotoolbox 
* django\_mongodb\_engine
* lxml
* rdflib 3.2.0+
* rdflib-jsonld
* Pymongo
* Pylucene 3.6.2
* paypalpy 
* django-crontab
* wkhtml2pdf

Installation
------------

The Web Server, MongoDB, wkhtml2pdf, python and pip itself can be installed using the 
package management tools provided by your operating system or using the available installers.

In order to install python and django dependences you can execute the script setup.sh.
This script will create a virtual environment for the project with the corresponding
packages, resolve all needed python and django dependences, and execute a complete test in order to ensure that 
WStore is correctly installed. To use this script you need virtualenv2.7 and python 2.7.

The script setup.sh download, extract and install pylucene 3.6.2 package. To do 
that setup.sh uses pylucene-install.sh and pylucene-patch-make-env.sh. This scripts install
lucene for a Ubuntu 11.10 like configuration, this cofiguration is setup in the pylucene-patch-make-env.sh 
script that modifies pylucene Makefile uncommenting and modifying the corresponding lines. 
The default configuartion is:

    # Linux     (Ubuntu 11.10 64-bit, Python 2.7.2, OpenJDK 1.7, setuptools 0.6.16)
    # Be sure to also set JDK['linux2'] in jcc's setup.py to the JAVA_HOME value
    # used below for ANT (and rebuild jcc after changing it).
    PREFIX_PYTHON=<wstore_path>/virtenv
    ANT=JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64 /usr/bin/ant
    PYTHON=$(PREFIX_PYTHON)/bin/python
    JCC=$(PYTHON) -m jcc --shared
    NUM_FILES=4

If you have a different enviroment you can modify pylucene-patch-make-env.sh to uncomment and 
modify the lines that match with your environment. Note that the PREFIX\_PYTHON variable is 
pointing to the python executable in your system by default; however, if you are using the 
provided scripts or a virtualenv by your own, you have to modify this variable to point to 
the python executable in your virtualenv, as can be seen in the example above.

If you do not want to modify this script, you can manually execute the script python-dep-install.sh
to resolve python dependences, manually install pylucene 3.6.2. and then, executng coverage.sh to 
perform the test. Note that the virtualenv is created in the setup.sh script so if you want to use 
a virtual environment you will need to install and activate it manually before installing any component;
otherwise, you will need to provide superuser credentials and all dependences will be installed in 
your system.

To manually install pylucene package have a look to pylucene documentation:

* http://lucene.apache.org/pylucene/install.html

Note that you will need to resolve Pylucene dependences (Java, ANT) before installing WStore, as can
be seen above, pyluene is configured to work with openjdk-7 as Java virtual machine. If you want
to use a different vm you will need to configure it manually as stated before.

WStore uses wkhtml2pdf for the creation of invoices, this software requires an X Server to work. If 
you do not have one, WStore will try to run Xvfb on the display :98. To install Xvfb use the following
command.

    $ apt-get install xvfb

For instructions on how to install WStore manually, without using any script, have a look at:

* http://forge.fi-ware.eu/plugins/mediawiki/wiki/fiware/index.php/Store\_-\_W-Store\_-\_Installation\_and\_Administration\_Guide


### Troubleshooting

The installation of lxml using pip can fail. This may occur because lxml headers for
compilation are missing, to avoid this problem you can install them manually before
installing lxml itself by executing:

    $ apt-get install libxslt1-dev

Installation of JCC when installing pylucene requires python headers. if they are 
not installed, you can install them by executing:

    $ apt-get install python2.7-dev


Configuration
-------------

### Database Configuration

The preliminary configuration of the database connection is included in settings.py and is 
ready to work using MongoDB in the default host and port, with a database called wstore\_db, 
and without security. To modify the database connection configuration edit the DATABASES setting:

<pre>
DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_engine',
        'NAME': 'wstore_db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST_NAME': 'test_database',
    }
}
</pre>

Using this setting is possible to change the database name and the test database name, 
include an user and password, and specify the host and port of MongoDB.

**Note**: The engine field cannot be changed, since WStore only works with MongoDB.

### Creating the deafult site

WStore (and any software using django\_mongodb\_engine and django sites framework) requires 
the creation of a default Site model. To create the default site, open WStore shell:

    $ python manage.py shell

Create the Site model including the information of the domain where WStore is going to run. 

<pre>
In [1]: from django.contrib.sites.models import Site

In [2]: Site.objects.create(name='local', domain='http://localhost:8000')
Out[2]: <Site: http://localhost:8000>
</pre>

Get the default site id:

    $ python manage.py tellsiteid

Include the site id in settings.py updating the SITE\_ID setting:

    SITE_ID = u'515ab0738e05ac20b622888b'
 
### PayPal Credentials Configuration

WStore uses PayPal to perform chargings. In order to receive the payments, it is 
necessary to include the credentials of a Business PayPal account in the settings.py 
file. In this file is also possible to configure the endpoints used by PayPal, 
this settings contain by default the testing sandbox endpoints.


    # Paypal creadetials
    PAYPAL_USER = '<PayPal_user_name>'
    PAYPAL_PASSWD = '<PayPal_password>'
    PAYPAL_SIGNATURE = '<PayPal_signature>'
    PAYPAL_URL = 'https://api-3t.sandbox.paypal.com/nvp'
    PAYPAL_CHECKOUT_URL='https://www.sandbox.paypal.com/webscr?cmd=_express-checkout'


### Pay-Per-Use Cron Configuration

WStore uses a Cron task to perform the aggregation and charging of Pay-per-use information. 
The periodicity of this task can be configured using the CRONJOBS setting of settings.py 
using the standard Cron format.

<pre>
CRONJOBS = [
    ('0 5 * * *', 'django.core.management.call_command', ['resolve_use_charging']),
]
</pre>

Once the Cron task has been configured, it is necessary to include it in the Cron 
tasks using the command: 

    $ python manage.py crontab add

It is also possible to show current jobs or remove jobs using the commands:

    $ python manage.py crontab show
 
    $ python manage.py crontab remove

### Authentication method Configuration

WStore allows two different methods for the authentication of users. The 
method for users management should be selected in the initial configurantion
of the WStore instance. Note that WStore does not store exactly the same info 
for the two methods, so, changing between authentication methods when the 
system has started to be used may cause unexpected behaviours.


#### FI-WARE Identity management

It is possible to delegate the authentication of users to the FI-WARE Identity 
Management system on a FI-WARE instance. View FI-LAB info in:

* http://lab.fi-ware.eu

To do that, the first step is setting up the OILAUTH setting
to True (Note that this is the default value).

    OILAUTH=True

Then configure the authentication endpoints in the file social\_auth\_backend.py:

<pre>
FIWARE_AUTHORIZATION_URL = 'https://fiware_idm_url/authorize'
FIWARE_ACCESS_TOKEN_URL = 'https://fiware_idm_url/token'
FIWARE_USER_DATA_URL = 'https://fiware_url_idm/user'
FIWARE_NOTIFICATION_URL = 'https://fiware_idm_url/purchases'
FIWARE_APPLICATIONS_URL = 'https://fiware_idm_url/applications.json'
</pre>

Next, register WStore as an application in the identity management portal, to do that
WStore uses the following URL as as callback URL for OAuth2 authentication:

    <host_wstore>/complete/fiware 

Once you have registered your WStore instance, get OAuth2 credentials needed for the 
authenticacion of your application. You will need to create two roles in your 
application, one for offering provider and other for offering customer. This roles 
will be used in the organizations with access to your WStore instance in order to grant
organization user the corresponding rights for purchasing and creating offerings for a 
complete organizations. To include the name you have specified for that roles, you have 
to fill the following settings in social\_auth\_backend.py:

    FIWARE_PROVIDER_ROLE='Name of the role'
    FIWARE_CUSTOMER_ROLE='Name of the role' 

Finally, include OAuth2 credentials in your WStore instance by filling the settings:

    FIWARE_APP_ID = client_id_number
    FIWARE_API_SECRET = client_secret


Note, that if you  use this method, all users registered in the corresponding FI-WARE
instance will have access to your application.

#### WStore Identity Management

WStore has its own authentication mechanism based on django auth. To enable WStore 
authentication, set up the OILAUTH setting to False:

    OILAUTH=False

For API accesses, WStore has an OAuth2 server that can be enabled by including the
oauth2provider in the INSTALLED\_APPS setting.

Applications can be registered in WStore using the django admin view.

### Database Population

Before running WStore, it is necessary to populate the database. This can be achieved 
by using this command:

    $ python manage.py syncdb

This command creates indexes for the different models of the database and ask if you 
want to create a Django superuser. In case you are using WStore authentication, this 
superuser is required in order to perform administrative tasks. If you are using FI-WARE 
authentication, users are taken from the identity management system, so do not create the user.
Users with corresponding role (Provider) will be able to perform the administrative tasks.

An example of the output of this command follows:

<pre>
...

You just installed Django's auth system, which means you don't have any superusers defined.
Would you like to create one now? (yes/no): yes
Username (leave blank to use 'francisco'): admin
E-mail address: admin@email.com   
Password: ***** (admin)
Password (again): ***** (admin)
Superuser created successfully.

...
</pre>


Final Steps
-----------

Make sure that the directories wstore\_path/src/media, wstore\_path/src/media/resources, 
wstore\_path/src/media/bills, wstore\_path/src/wstore/search/indexes  exist, and that the 
server has sufficient permissions to write on them. To do so use the following commands: 

    # chgrp -R www-data  wstore_path/src/media wstore_path/src/wstore/search/indexes

    # chmod g+wrX -R <wstore_path>/src/media wstore_path/src/wstore/search/indexes

it is possible to collect all static files in WStore in a single directory using the 
following command and answering yes when asked.

    $ python manage.py collectstatic

Running WStore
--------------

### Running WStore using the Django internal web server

Be aware that this way of running WStore should be used for evaluation purposes.
Do not use it in a production environment. To start WStore, type the following command: 

    $ python manage.py runserver 0.0.0.0:8000

Then, go to http://computer\_name\_or\_IP\_address:8000/ where computer\_name\_or\_IP\_address 
is the name or IP address of the computer on which WStore is installed.


### Integrating WStore with Apache

if you choose to deploy WStore in Apache, the libapache2-mod-wsgi module must be installed 
(and so does Apache!). To do so, type the following command: 

    $ apt-get install apache2 libapache2-mod-wsgi

Then you have to populate the wsgi.py file:

<pre>
 import os
 import sys
 path = 'path_to_wstore/src'
 if path not in sys.path:
     sys.path.insert(0, path)
 os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
 import django.core.handlers.wsgi
 application = django.core.handlers.wsgi.WSGIHandler()
</pre>

If you are running WStore using a virtualenv environment (for example if you have installed the 
dependencies using the provided script) your wsgi.py file sholud have the following structure:

<pre>

import os
import sys
import site

site.addsitedir('vitualenv_path/local/lib/python2.7/site-packages')
path = 'path_to_wstore/src'
if path not in sys.path:
    sys.path.insert(0, path)
   
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Activate your virtual env
activate_env=os.path.expanduser("vitualenv_path/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
</pre>

Please, pay attention that you set the right path to the wtore/src directory. 

Finally, add the following lines in the main virtualhost to the Apache's 
sites-available configuration file, usually located in /etc/apache2/sites-available/default:

    <VirtualHost *:80>
            ...
            ### WStore ###
            WSGIScriptAlias / <path_to_django_wsgi>
            WSGIPassAuthorization On
            Alias /static <path_to_wstore>/src/static>
            <Location "/static">
                    SetHandler None
                    <IfModule mod_expires.c>
                            ExpiresActive On
                            ExpiresDefault "access plus 1 week"
                    </IfModule>
                    <IfModule mod_headers.c>
                            Header append Cache-Control "public"
                    </IfModule>
            </Location>
            <Location "/static/cache">
                    <IfModule mod_expires.c>
                            ExpiresDefault "access plus 3 years"
                    </IfModule>
            </Location>
            ...
    </VirtualHost>

Again, pay special attention to the paths to the django wsgi file and the 
path\_to\_wstore/src/static directory. 

Once you have the site enabled, restart Apache

    # service apache2 restart

Extra documentation
-------------------

Open API specification:

* http://forge.fi-ware.eu/plugins/mediawiki/wiki/fiware/index.php/Storei\_Open\_API\_RESTful\_Specification

User and Programmer Guide:

* http://forge.fi-ware.eu/plugins/mediawiki/wiki/fiware/index.php/Store\_-\_W-Store\_-\_User\_and\_Programmer\_Guide


