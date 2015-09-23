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

from wstore.rss_adaptor.expenditure_manager import ExpenditureManagerV1, ExpenditureManagerV2
from wstore.rss_adaptor.model_manager import ModelManagerV1, ModelManagerV2
from wstore.rss_adaptor.rss_manager import ProviderManager
from wstore.rss_adaptor.rss_adaptor import RSSAdaptorV1, RSSAdaptorV2


class RSSManagerFactory():

    def __init__(self, rss):
        self._rss = rss

    def get_expenditure_manager(self, credentials):
        managers = {
            1: ExpenditureManagerV1,
            2: ExpenditureManagerV2
        }
        return managers[self._rss.api_version](self._rss, credentials)

    def get_model_manager(self, credentials):
        managers = {
            1: ModelManagerV1,
            2: ModelManagerV2
        }
        return managers[self._rss.api_version](self._rss, credentials)

    def get_rss_adaptor(self):
        adaptors = {
            1: RSSAdaptorV1,
            2: RSSAdaptorV2
        }
        return adaptors[self._rss.api_version](self._rss)

    def get_provider_manager(self, credentials):
        return ProviderManager(self._rss, credentials)
