
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
         "default": "default vendor",
         "label": "Vendor"
      },
      "name": {
         "type": "text",
         "placeholder": "Name",
         "default": "default name",
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
          "default": "default value",
          "placeholder": "placeholder"
      }
  }
}

PLUGIN_INFO2 = {
    "name": "test plugin 5",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "formats": ["FILE"]
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

INVALID_OVERRIDES = {
    "name": "plugin name",
    "author": "test author",
    "version": "1.0",
    "module": "test.TestPlugin",
    "media_types": ["text/plain"],
    "formats": ["FILE", "URL"],
    "overrides": ["INVALID"]
}