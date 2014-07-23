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


def version_cmp(version1, version2):
    result = 0

    if not '.' in version1 and version1.isdigit():
        version1 += '.0'

    if not '.' in version2 and version2.isdigit():
        version2 += '.0'

    if StrictVersion(version1) < StrictVersion(version2):
        result = -1
    elif StrictVersion(version1) > StrictVersion(version2):
        result = 1

    return result


def key_fun_version(comparator, object_instance=False):

    class key(object):
        def __init__(self, obj, *args):
            self.obj = obj
            if object_instance:
                self.obj = obj.version

        def __lt__(self, other):
            return comparator(self.obj, other.obj) < 0

        def __gt__(self, other):
            return comparator(self.obj, other.obj) > 0

        def __eq__(self, other):
            return comparator(self.obj, other.obj) == 0

        def __le__(self, other):
            return comparator(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return comparator(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return comparator(self.obj, other.obj) != 0

    return key
