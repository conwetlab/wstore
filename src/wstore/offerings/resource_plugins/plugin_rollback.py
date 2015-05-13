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

from shutil import rmtree

from functools import wraps


def installPluginRollback(func):

    class Logger():
        _state = {}

        def get_state(self):
            return self._state

        def log_action(self, action, value):
            self._state[action] = value

    @wraps(func)
    def wrapper(self, path, logger=None):
        try:
            logger = Logger()
            result = func(self, path, logger=logger)
        except Exception as e:
            # Remove directory if existing
            if 'PATH' in logger.get_state():
                rmtree(logger.get_state()['PATH'], True)

            # Raise the exception
            raise(e)
        return result

    return wrapper
