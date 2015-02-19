
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

from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.offerings.resource_plugins.plugin_manager import PluginManager


PLUGIN_INFO = {
  "name": "test plugin",
  "author": "test author",
  "version": "1.0",
  "module": "test.TestPlugin",
  "media_types": [
      "application/x-widget+mashable-application-component",
      "application/x-mashup+mashable-application-component",
      "application/x-operator+mashable-application-component"
  ],
  "formats": ["FILE"],
  "form": {
      "vendor": {
         "type": "text",
         "placeholder": "Vendor",
         "default": "Default vendor",
         "label": "Vendor"
      },
      "name": {
         "type": "text",
         "placeholder": "Name",
         "default": "Default name",
         "label": "Name",
         "mandatory": True
      },
      "type": {
          "type": "select",
          "label": "Select",
          "options": [{
              "text": "Option 1",
              "value": "opt1"
          }, {
              "text": "Option 2",
              "value": "opt2"
          }]
      },
      "is_op": {
          "type": "checkbox",
          "label": "Is a checkbox",
          "text": "The checkbox",
          "default": True
      },
      "area": {
          "type": "textarea",
          "label": "Area",
          "default": "A text area",
          "placeholder": "A text area"
      }
  },
  "options": {}
}

MISSING_NAME = {
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE"]
}

INVALID_NAME = {
    "name": "inv&name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE"]
}

MISSING_AUTHOR = {
    "name": "plugin name",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE"]
}

MISSING_FORMATS = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": []
}

MISSING_MODULE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "media_types": [],
    "formats": ["FILE"]
}

MISSING_VERSION = {
    "name": "plugin name",
    "author": "test author",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE"]
}

INVALID_NAME_TYPE = {
    "name": 9,
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE"]
}

INVALID_AUTHOR_TYPE = {
    "name": "plugin name",
    "author": 10,
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE"]
}

INVALID_FORMAT_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": "FILE"
}

INVALID_FORMAT = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": [],
    "formats": ["FILE", "URL", "INV"]
}

INVALID_MEDIA_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": "text/plain",
    "formats": ["FILE", "URL"]
}

INVALID_MODULE_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": [],
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"]
}

INVALID_VERSION = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.a",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"]
}

INVALID_VERSION = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.a",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"]
}

INVALID_FORM_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "form": ""
}

INVALID_FORM_ENTRY_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "form": {
        "name": "input"
    }
}

INVALID_FORM_MISSING_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "form": {
        "name": {
            "placeholder": "Name",
            "default": "Default name",
            "label": "Name",
            "mandatory": True
        }
    }
}

INVALID_FORM_INV_TYPE = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "form": {
        "name": {
            "type": "invalid",
            "placeholder": "Name",
            "default": "Default name",
            "label": "Name",
            "mandatory": True
        }
    }
}

INVALID_FORM_INVALID_NAME = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "form": {
        "inv&name": {
            "type": "text",
            "placeholder": "Name",
            "default": "Default name",
            "label": "Name",
            "mandatory": True
        }
    }
}

INVALID_FORM_CHECKBOX_DEF = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "form": {
        "check": {
            "type": "checkbox",
            "default": "Default name",
            "label": "Name"
        }
    }
}


class PluginLoaderTestCase(TestCase):

    @parameterized.expand([
        ()
    ])
    def test_plugin_installation(self):
        pass

    @parameterized.expand([
        ()
    ])
    def test_plugin_removal(self):
        pass


class PluginValidatorTestCase(TestCase):

    tags = ('plugin', )

    @parameterized.expand([
        ('correct', PLUGIN_INFO),
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
        ('invalid_form_checkbox_def', INVALID_FORM_CHECKBOX_DEF, 'Invalid form field: default field in check entry must be a boolean')
    ])
    def test_plugin_info_validation(self, name, plugin_info, validation_msg=None):

        plugin_manager = PluginManager()

        reason = plugin_manager.validate_plugin_info(plugin_info)
        self.assertEquals(reason, validation_msg)
