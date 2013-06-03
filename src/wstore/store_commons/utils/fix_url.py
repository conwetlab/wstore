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

import urllib
import urlparse

def url_fix(s, charset='utf-8'):
    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')

    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)

    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')

    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))
