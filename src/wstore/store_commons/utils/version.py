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

from distutils.version import StrictVersion


def is_lower_version(version1, version2):
    # Strict version does not allow single number as versions
    # so it is needed to fix them
    if not '.' in version1 and version1.isdigit():
        version1 += '.0'

    if not '.' in version2 and version2.isdigit():
        version2 += '.0'

    return StrictVersion(version1) < StrictVersion(version2)