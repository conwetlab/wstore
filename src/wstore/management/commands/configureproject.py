# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.

import os
import codecs
from sys import stdin
import subprocess

import django.conf
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand
from django.template import loader, Context


from wstore.store_commons.database import get_database_connection
from wstore.store_commons.utils.url import is_valid_url


def exec_external_cmd(cmd):
    result = subprocess.call(cmd, shell=True)
    if result:
        raise CommandError('Error executing external command')


def read_from_cmd():
    return stdin.readline()[:-1]


def get_yes_no_option(msg):
    correct = False
    while not correct:
        print msg + " [y/n]:"
        opt = read_from_cmd()
        if opt != 'y' and opt != 'n':
            print "Please include 'y' or 'n'"
            continue
        correct = True

    return opt


def get_url(msg):
    correct = False
    while not correct:
        print msg
        domain = read_from_cmd()

        if not is_valid_url(domain):
            print "The domain " + domain + " is not a valid URL"
        else:
            correct = True

    return domain


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        Starts and configures a new WStore instance
        """

        # Check if the user want to create an initial configuration
        opt = get_yes_no_option("Do you want to create an initial configuration")

        if opt == 'n':
            print "You can configure WStore manually editing settings.py file"
            read_from_cmd()
            return

        settings = {
            'email_user': 'email_user',
            'wstore_email': 'wstore_email',
            'wstore_email_passwd': 'wstore_email_passwd',
            'email_smtp_server': 'wstore_smtp_server',
            'provider_req_email': 'provider_requ_email',
            'client_id': 0,
            'client_secret': 'Client_secret',
            'oilauth': False,
            'idm_endpoint': 'idm_endpoint'
        }

        # Get database name
        print "Include a database name: "
        settings['database'] = read_from_cmd()

        # Create the default site
        print "Include a site name: "
        site_name = read_from_cmd()

        site_domain = get_url("Include a site domain: ")

        # Get WStore name
        print "Include a name for your instance: "
        settings['store_name'] = read_from_cmd()

        option = get_yes_no_option("Do you want to include email configuration?")

        if option == 'y':
            print "Include email smtp server endpoint: "
            settings['provider_req_email'] = read_from_cmd()

            print "Include WStore email: "
            settings['wstore_email'] = read_from_cmd()

            print "Include WStore email user: "
            settings['email_user'] = read_from_cmd()

            print "Include WStore email password: "
            settings['wstore_email_passwd'] = read_from_cmd()

            print "Include WStore provider requests email: "
            settings['provider_req_email'] = read_from_cmd()

        correct = False
        while not correct:
            # Select authentication method
            print "Select authentication method: "
            print "1) Identity manager"
            print "2) WStore"

            option = read_from_cmd()
            try:
                number_opt = int(option)
            except:
                print "Invalid option. Please select 1 or 2"
                continue

            if number_opt != 1 and number_opt != 2:
                print "Invalid option. Please select 1 or 2"
                continue

            correct = True

        syn_command = 'python manage.py syncdb'
        # Get auth info
        if number_opt == 1:
            print "Include Identity manager endpoint: (default https://account.lab.fiware.org/)"
            settings['oilauth'] = True

            settings['idm_endpoint'] = read_from_cmd()

            if not len(settings['idm_endpoint']) or settings['idm_endpoint'].isspace():
                settings['idm_endpoint'] = "https://account.lab.fiware.org/"

            syn_command += ' --noinput'

            # Get idm api version
            correct = False
            while not correct:
                print "Include KeyRock API version [1/2]: "
                api_version = read_from_cmd()
                if api_version.isdigit() and (int(api_version) == 1 or int(api_version) == 2):
                    settings['idm_api_version'] = int(api_version)
                    correct = True
                else:
                    print "Please include 1 or 2"

            if settings['idm_api_version'] == 2:
                if settings['idm_endpoint'].startswith('https://account.lab.fiware.org'):
                    settings['keystone_endpoint'] = "http://cloud.lab.fiware.org:4731"
                else:
                    settings['keystone_endpoint'] = get_url("Include KeyStone endpoint: ")

            option = get_yes_no_option("Do you want to include OAuth2 configuration?")

            if option == 'y':
                print "Include Client id: "
                settings['client_id'] = read_from_cmd()
                print "Include client secret:"
                settings['client_secret'] = read_from_cmd()
            else:
                print """OAuth2 credentials are required for authentication using an Identity Manager, 
                please include this credentials in the file settings.py as soon as you have them"""
        else:
            settings['idm_api_version'] = 2

        # Render templates

        template = loader.get_template('conf/settings_template.py')
        settings_content = template.render(Context(settings))

        # Create intermediate settings file
        f = codecs.open(os.path.join(django.conf.settings.BASEDIR, 'settings.py'), "wb", 'utf-8')
        f.seek(0)
        f.write(settings_content)
        f.truncate()
        f.close()

        # Execute final commands
        exec_external_cmd(syn_command)
        exec_external_cmd('python manage.py collectstatic --noinput')
        exec_external_cmd('python manage.py createsite ' + site_name + ' ' + site_domain)

        # Reload the settings
        reload(django.conf)

        # Get site pk to include it as site_id, raw mongo access since it is not
        # possible to change the database dynamically
        db = get_database_connection()
        settings['site_id'] = unicode(db.django_site.find_one({'name': site_name})['_id'])

        # Create final settings file including site_id
        settings_content = template.render(Context(settings))

        # Create final settings file
        f = codecs.open(os.path.join(django.conf.settings.BASEDIR, 'settings.py'), "wb", 'utf-8')
        f.seek(0)
        f.write(settings_content)
        f.truncate()
        f.close()
