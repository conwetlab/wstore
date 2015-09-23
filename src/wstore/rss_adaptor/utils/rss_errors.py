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


ERROR_CODES = {
    'SVC1006': 'The current instance of WStore is not registered in the Revenue Sharing System, so it is not possible to access RSS APIs. Please contact with the administrator of the RSS.'
}


def get_error_message(code):
    result = 'An error occurs when accessing the RSS'
    if code in ERROR_CODES:
        result = ERROR_CODES[code]
    return result
