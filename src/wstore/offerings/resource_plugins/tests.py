
# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

from __future__ import unicode_literals

import os
from mock import MagicMock
from nose_parameterized import parameterized
from shutil import rmtree

from django.test import TestCase
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

from wstore.offerings.resource_plugins.plugin_manager import PluginManager
from wstore.offerings.resource_plugins.plugin_error import PluginError
from wstore.offerings.resource_plugins import plugin_loader
from wstore.models import ResourcePlugin
from wstore.offerings.resource_plugins.test_data import *


class PluginLoaderTestCase(TestCase):

    tags = ('plugin', )

    _to_remove = None

    def setUp(self):
        # Create PluginManager mock
        plugin_loader.PluginManager = MagicMock(name="PluginManager")
        self.manager_mock = MagicMock()
        self.manager_mock.validate_plugin_info.return_value = None

        plugin_loader.PluginManager.return_value = self.manager_mock

    def _remove_plugin_dir(self, plugin_name):
        plugin_dir = os.path.join(os.path.join('wstore', 'test'), plugin_name)
        rmtree(plugin_dir, True)

    def tearDown(self):
        # Remove created plugin dir if needed
        try:
            os.remove(os.path.join(self.plugin_dir, '__init__.py'))
            self._remove_plugin_dir(self._to_remove.split('.')[0].replace('_', '-'))
        except:
            pass

    def _inv_zip(self):
        self.zip_path = 'wstore'

    def _inv_plugin_info(self):
        self.manager_mock.validate_plugin_info.return_value = 'validation error'

    def _existing_plugin(self):
        ResourcePlugin.objects.create(
            name='test plugin',
            plugin_id='test-plugin',
            version='1.0',
            author='test author',
            module='test-plugin.TestPlugin'
        )

    @parameterized.expand([
        ('correct', 'test_plugin.zip', PLUGIN_INFO),
        ('correct_no_optionals', 'test_plugin_5.zip', PLUGIN_INFO2),
        ('invalid_zip', 'test_plugin.zip', None, _inv_zip, PluginError, 'Plugin Error: Invalid package format: Not a zip file'),
        ('missing_json', 'test_plugin_2.zip', None, None, PluginError, 'Plugin Error: Missing package.json file'),
        ('not_plugin_imp', 'test_plugin_3.zip', None, None, PluginError, 'Plugin Error: No Plugin implementation has been found'),
        ('inv_json', 'test_plugin_4.zip', None, None,  PluginError, 'Plugin Error: Invalid format in package.json file. JSON cannot be parsed'),
        ('validation_err', 'test_plugin.zip', None,  _inv_plugin_info, PluginError, 'Plugin Error: Invalid format in package.json file. validation error'),
        ('existing', 'test_plugin.zip', None,  _existing_plugin, PluginError, 'Plugin Error: A plugin with the same id (test-plugin) already exists')
    ])
    def test_plugin_installation(self, name, zip_file, expected=None, side_effect=None, err_type=None, err_msg=None):
        # Build plugin loader
        plugin_l = plugin_loader.PluginLoader()

        self.plugin_dir = os.path.join('wstore', 'test')

        # Mock plugin directory location
        plugin_l._plugins_path = self.plugin_dir
        plugin_l._plugins_module = 'wstore.test.'

        # Create a init file in the test dir
        open(os.path.join(self.plugin_dir, '__init__.py'), 'a').close()

        self.zip_path = os.path.join(self.plugin_dir, 'test_plugin_files')
        self.zip_path = os.path.join(self.zip_path, zip_file)

        if side_effect is not None:
            side_effect(self)

        self._to_remove = zip_file
        error = None
        try:
            plugin_l.install_plugin(self.zip_path)
        except Exception as e:
            error = e

        if err_type is None:
            self.assertEquals(error, None)
            # Check calls
            self.manager_mock.validate_plugin_info.assert_called_once_with(expected)

            # Check plugin model
            plugin_model = ResourcePlugin.objects.all()[0]
            self.assertEquals(plugin_model.name, expected['name'])
            self.assertEquals(plugin_model.plugin_id, expected['name'].lower().replace(' ', '-'))
            self.assertEquals(plugin_model.author, expected['author'])
            self.assertEquals(plugin_model.version, expected['version'])
            self.assertEquals(plugin_model.formats, expected['formats'])

            self.assertEquals(plugin_model.module, 'wstore.test.' + plugin_model.plugin_id + '.' + expected['module'])
            self.assertEquals(plugin_model.media_types, expected.get('media_types', []))
            self.assertEquals(plugin_model.form, expected.get('form', {}))

            # Check plugin files
            test_plugin_dir = os.path.join(self.plugin_dir, plugin_model.plugin_id)
            self.assertTrue(os.path.isdir(test_plugin_dir))
            self.assertTrue(os.path.isfile(os.path.join(test_plugin_dir, 'package.json')))
            self.assertTrue(os.path.isfile(os.path.join(test_plugin_dir, 'test.py')))

        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)

    def _plugin_in_use(self):
        plugin_loader.Resource.objects.filter.return_value = ['resource']

    def _plugin_not_exists(self):
        plugin_loader.ResourcePlugin.objects.get.side_effect = Exception('Not exists')

    @parameterized.expand([
        ('correct', ),
        ('plugin_used', _plugin_in_use, PermissionDenied, 'The plugin test_plugin is being used in some resources'),
        ('not_exists', _plugin_not_exists, ObjectDoesNotExist, 'The plugin test_plugin is not registered')
    ])
    def test_plugin_removal(self, name, side_effect=None, err_type=None, err_msg=None):

        # Mock libreries
        plugin_loader.Resource = MagicMock(name="Resource")

        self.resources_mock = MagicMock()
        plugin_loader.Resource.objects.filter.return_value = []

        plugin_loader.ResourcePlugin = MagicMock(name="ResourcePlugin")
        plugin_mock = MagicMock()
        plugin_loader.ResourcePlugin.objects.get.return_value = plugin_mock

        plugin_loader.rmtree = MagicMock(name="rmtree")

        if side_effect is not None:
            side_effect(self)

        # Build plugin loader
        plugin_l = plugin_loader.PluginLoader()

        error = None
        try:
            plugin_l.uninstall_plugin('test_plugin')
        except Exception as e:
            error = e

        if err_type is None:
            self.assertEquals(error, None)
            # Check calls
            plugin_loader.ResourcePlugin.objects.get.assert_called_once_with(plugin_id='test_plugin')
            plugin_loader.rmtree.assert_called_once_with(os.path.join(plugin_l._plugins_path, 'test_plugin'))
            plugin_mock.delete.assert_called_once_with()
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)


class PluginValidatorTestCase(TestCase):

    tags = ('plugin', )

    @parameterized.expand([
        ('correct', PLUGIN_INFO),
        ('invalid_type', 'invalid', 'Plugin info must be a dict instance'),
        ('missing_name', MISSING_NAME, 'Missing required field: name'),
        ('invalid_name', INVALID_NAME, 'Invalid name format: invalid character'),
        ('missing_author', MISSING_AUTHOR, 'Missing required field: author'),
        ('missing_formats', MISSING_FORMATS, 'Missing required field: formats'),
        ('missing_module', MISSING_MODULE, 'Missing required field: module'),
        ('missing_version', MISSING_VERSION, 'Missing required field: version'),
        ('invalid_name_type', INVALID_NAME_TYPE, 'Plugin name must be an string'),
        ('invalid_author_type', INVALID_AUTHOR_TYPE, 'Plugin author must be an string'),
        ('invalid_formats_type', INVALID_FORMAT_TYPE, 'Plugin formats must be a list'),
        ('invalid_format', INVALID_FORMAT, 'Format must contain at least one format of: FILE, URL'),
        ('invalid_media_type', INVALID_MEDIA_TYPE, 'Plugin media_types must be a list'),
        ('invalid_module_type', INVALID_MODULE_TYPE, 'Plugin module must be an string'),
        ('invalid_version', INVALID_VERSION, 'Invalid format in plugin version'),
        ('invalid_form_type', INVALID_FORM_TYPE, 'Invalid format in form field, must be an object'),
        ('invalid_form_entry_type', INVALID_FORM_ENTRY_TYPE, 'Invalid form field: name entry is not an object'),
        ('invalid_form_missing_type', INVALID_FORM_MISSING_TYPE, 'Invalid form field: Missing type in name entry'),
        ('invalid_form_inv_type', INVALID_FORM_INV_TYPE, 'Invalid form field: type invalid in name entry is not a valid type'),
        ('invalid_form_inv_name', INVALID_FORM_INVALID_NAME, 'Invalid form field: inv&name is not a valid name'),
        ('invalid_form_checkbox_def', INVALID_FORM_CHECKBOX_DEF, 'Invalid form field: default field in check entry must be a boolean'),
        ('invalid_overrides', INVALID_OVERRIDES, 'Override values should be one of: NAME, VERSION and OPEN')
    ])
    def test_plugin_info_validation(self, name, plugin_info, validation_msg=None):

        plugin_manager = PluginManager()

        reason = plugin_manager.validate_plugin_info(plugin_info)
        self.assertEquals(reason, validation_msg)
