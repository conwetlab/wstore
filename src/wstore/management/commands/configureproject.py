# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

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
from pymongo import MongoClient
from sys import stdin
import subprocess

import django.conf
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand
from django.template import loader, Context


def exec_external_cmd(cmd):
    result = subprocess.call(cmd, shell=True)
    if result:
        raise CommandError('Error executing external command')


def read_from_cmd():
    return stdin.readline()[:-1]


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        Starts and configures a new WStore instance
        """
        # Check if the user want to create an initial configuration
        correct = False
        while not correct:
            print "Do you want to create an initial configuration? [y/n]:"
            opt = read_from_cmd()
            if opt != 'y' and opt != 'n':
                print "Please include 'y' or 'n'"
                continue
            correct = True

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
        print "Include a site domain: "
        site_domain = read_from_cmd()

        # Get WStore name
        print "Include a name for your instance: "
        settings['store_name'] = read_from_cmd()

        correct = False
        while not correct:
            # Get optional mail configuration
            print "Do you want to include email configuration? [y/n]: "
            option = read_from_cmd()
            if option != 'y' and option != 'n':
                print "Please include 'y' or 'n'"
                continue
            correct = True

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
            print "Include Identity manager endpoint: "
            settings['oilauth'] = True
            settings['idm_endpoint'] = read_from_cmd()
            syn_command +=  ' --noinput'

            correct = False
            while not correct:
                # Get optional mail configuration
                print "Do you want to include OAuth2 configuration? [y/n]: "
                option = read_from_cmd()
                if option != 'y' and option != 'n':
                    print "Please include 'y' or 'n'"
                    continue
                correct = True

            if option == 'y':
                print "Include Client id: "
                settings['client_id'] = read_from_cmd()
                print "Include client secret:"
                settings['client_secret'] = read_from_cmd()
            else:
                print """OAuth2 credentials are required for authentication using an Identity Manager, 
                please include this credentials in the file settings.py as soon as you have them"""

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
        client = MongoClient()
        db = client[settings['database']]
        settings['site_id'] = unicode(db.django_site.find_one({'name': site_name})['_id'])

        # Create final settings file including site_id
        settings_content = template.render(Context(settings))

        # Create intermediate settings file
        f = codecs.open(os.path.join(django.conf.settings.BASEDIR, 'settings.py'), "wb", 'utf-8')
        f.seek(0)
        f.write(settings_content)
        f.truncate()
        f.close()
