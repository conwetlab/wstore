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

from __future__ import unicode_literals

BASIC_OFFERING = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

BASIC_EXPECTED = {
    'image': '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0'
}

OFFERING_BIGGER_VERSION = {
    'name': 'test_offering',
    'version': '3.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

EXPECTED_BIGGER_VERSION = {
    'image': '/media/test_organization__test_offering__3.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__3.0'
}

OFFERING_WITH_IMAGES = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [{
        'name': 'test_screen1.png',
        'data': ''
    },
    {
        'name': 'test_screen2.png',
        'data': ''
    }],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

EXPECTED_WITH_IMAGES = {
    'image':  '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0',
    'screenshots': [
        '/media/test_organization__test_offering__1.0/test_screen1.png',
        '/media/test_organization__test_offering__1.0/test_screen2.png'
    ]
}

OFFERING_USDL_DATA = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test offering',
        'pricing': {
            'price_model': 'free'
        }
    }
}

OFFERING_USDL_DATA_COMPLETE = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test offering',
        'pricing': {
            'price_model': 'single_payment',
            'price': 5
        },
        'legal': {
            'title': 'legal title',
            'text': 'legal text'
        }
    }
}

OFFERING_URL = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'description_url': 'http://examplerep/v1/test_usdl'
}

EXPECTED_URL = {
    'image': '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://examplerep/v1/test_usdl'
}

OFFERING_APPLICATIONS_RESOURCES = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    },
    'applications': [{
        'name': 'test_app1',
        'url': 'http://test_app1.com',
        'id': 1,
        'description': 'a test application'
    }],
    'resources': [{
        'name': 'test_res',
        'description': 'a test resource'
    }]
}

OFFERING_NOTIFY_URL = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'notification_url': 'http://notification_url.com',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_NOTIFY_DEFAULT = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'notification_url': 'default',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

EXPECTED_NOTIFY_URL = {
    'image': '/media/test_organization__test_offering__1.0/test_image.png',
    'description_url': 'http://testrepository/storeOfferingCollection/test_organization__test_offering__1.0',
    'notification_url': 'http://notification_url.com'
}

OFFERING_INVALID_VERSION = {
    'name': 'test_offering',
    'version': '1.0.',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_INVALID_NAME = {
    'name': '.name',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_INVALID_JSON = {
    'na': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_NOTIFY_URL_INVALID = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'notification_url': 'invalid url',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_EXISTING = {
    'name': 'test_offering_fail',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_NO_USDL = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    }
}

OFFERING_NO_IMAGE = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_IMAGE_INVALID = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': '',
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_IMAGE_MISSING = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
    },
    'offering_description': {
        'content_type': 'application/rdf+xml',
        'data': ''
    }
}

OFFERING_USDL_DATA_INVALID = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'pricing': {
            'price_model': 'free'
        }
    }
}

OFFERING_USDL_DATA_INVALID_1 = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': '',
        'pricing': {
            'price_model': 'free'
        }
    }
}

OFFERING_USDL_DATA_INVALID_2 = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test usdl description',
        'pricing': {
            'price_model': 'free'
        },
        'legal': {
        }
    }
}

OFFERING_USDL_DATA_INVALID_3 = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test usdl description',
        'pricing': {
            'price_model': 'free'
        },
        'legal': {
            'title': '',
            'text': 'some text'
        }
    }
}

OFFERING_USDL_DATA_INVALID_4 = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test usdl description',
        'pricing': {
            'price': 5
        }
    }
}

OFFERING_USDL_DATA_INVALID_5 = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test usdl description',
        'pricing': {
            'price_model': 'single_payment'
        }
    }
}

OFFERING_USDL_DATA_INVALID_6 = {
    'name': 'test_offering',
    'version': '1.0',
    'repository': 'test_repository',
    'image': {
        'name': 'test_image.png',
        'data': '',
    },
    'related_images': [],
    'offering_info': {
        'description': 'Test usdl description',
        'pricing': {
            'price_model': 'single_payment',
            'price': ''
        }
    }
}