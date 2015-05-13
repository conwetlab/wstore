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

import re
import regex
from distutils.version import StrictVersion
from six import string_types


def is_valid_version(version):
    valid = True

    if not re.match(re.compile(r'^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$'), version):
        valid = False

    return valid


def is_lower_version(version1, version2):
    # Strict version does not allow single number as versions
    # so it is needed to fix them
    if '.' not in version1 and version1.isdigit():
        version1 += '.0'

    if '.' not in version2 and version2.isdigit():
        version2 += '.0'

    return StrictVersion(version1) < StrictVersion(version2)


def version_cmp(version1, version2):
    result = 0

    if '.' not in version1 and version1.isdigit():
        version1 += '.0'

    if '.' not in version2 and version2.isdigit():
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


class Version(object):

    version_re = regex.compile(r'^([1-9]\d*|0)((?:\.(?:[1-9]\d*|0))*)(?:(a|b|rc)([1-9]\d*))?$')

    def __init__(self, vstring, reverse=False):

        match = self.version_re.match(vstring)

        if not match:
            raise ValueError("Invalid version number '%s'" % vstring)

        (major, patch, prerelease, prerelease_num) = match.group(1, 2, 3, 4)

        if patch:
            self.version = tuple(map(int, [major] + patch[1:].split('.')))
        else:
            self.version = (int(major),)

        if prerelease:
            self.prerelease = (prerelease, int(prerelease_num))
        else:
            self.prerelease = None

        self.reverse = reverse

    def __cmp__(self, other):

        if isinstance(other, string_types):
            other = Version(other)

        if not isinstance(other, Version):
            raise ValueError("Invalid version number '%s'" % other)

        maxlen = max(len(self.version), len(other.version))
        compare = cmp(self.version + (0,)*(maxlen - len(self.version)), other.version + (0,)*(maxlen - len(other.version)))

        if compare == 0:

            # case 1: neither has prerelease; they're equal
            if not self.prerelease and not other.prerelease:
                compare = 0

            # case 2: self has prerelease, other doesn't; other is greater
            elif self.prerelease and not other.prerelease:
                compare = -1

            # case 3: self doesn't have prerelease, other does: self is greater
            elif not self.prerelease and other.prerelease:
                compare = 1

            # case 4: both have prerelease: must compare them!
            elif self.prerelease and other.prerelease:
                compare = cmp(self.prerelease, other.prerelease)

        return compare if not self.reverse else (compare * -1)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0
