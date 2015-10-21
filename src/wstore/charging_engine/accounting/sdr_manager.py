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

from datetime import datetime

from django.core.exceptions import PermissionDenied

from wstore.models import Offering, Organization, User


class SDRManager(object):

    def __init__(self, purchase):
        self._purchase = purchase
        self._price_model = purchase.contract.pricing_model

    def include_sdr(self, sdr):
        # Check the offering and customer
        off_data = sdr['offering']
        org = Organization.objects.get(name=off_data['organization'])
        offering = Offering.objects.get(name=off_data['name'], owner_organization=org, version=off_data['version'])

        if offering != self._purchase.offering:
            raise PermissionDenied('The offering specified in the SDR is not the acquired offering')

        customer = User.objects.get(username=sdr['customer'])

        if self._purchase.organization_owned:
            # Check if the user belongs to the organization
            profile = customer.userprofile
            belongs = False

            for org in profile.organizations:
                if org['organization'] == self._purchase.owner_organization.pk:
                    belongs = True
                    break

            if not belongs:
                raise PermissionDenied('The user does not belong to the owner organization')
        else:
            # Check if the user has purchased the offering
            if customer != self._purchase.customer:
                raise PermissionDenied('The user has not acquired the offering')

        if 'pay_per_use' not in self._price_model:
            raise ValueError('The pricing model of the offering does not define pay-per-use components')

        # Check the correlation number and timestamp
        applied_sdrs = self._purchase.contract.applied_sdrs
        pending_sdrs = self._purchase.contract.pending_sdrs
        last_corr = 0

        last_time = None

        if len(pending_sdrs) > 0:
            last_corr = int(pending_sdrs[-1]['correlation_number'])
            last_time = pending_sdrs[-1]['time_stamp']
        else:
            if len(applied_sdrs) > 0:
                last_corr = int(applied_sdrs[-1]['correlation_number'])
                last_time = applied_sdrs[-1]['time_stamp']

        # Truncate ms to 3 decimals (database supported)
        sp_time = sdr['time_stamp'].split('.')
        milis = sp_time[1]

        if len(milis) > 3:
            milis = milis[:3]

        sdr_time = sp_time[0] + '.' + milis

        try:
            time_stamp = datetime.strptime(sdr_time, '%Y-%m-%dT%H:%M:%S.%f')
        except:
            time_stamp = datetime.strptime(sdr_time, '%Y-%m-%d %H:%M:%S.%f')

        if int(sdr['correlation_number']) != last_corr + 1:
            raise ValueError('Invalid correlation number, expected: ' + str(last_corr + 1))

        if last_time is not None and last_time > time_stamp:
            raise ValueError('The provided timestamp specifies a lower timing than the last SDR received')

        # Check unit or component_label depending if the model defines components or
        # price functions
        found_model = False
        for comp in self._price_model['pay_per_use']:
            if 'price_function' not in comp:
                if sdr['unit'] == comp['unit']:
                    found_model = True
                    break
            else:
                for k, var in comp['price_function']['variables'].iteritems():
                    if var['type'] == 'usage' and var['label'] == sdr['component_label']:
                        found_model = True
                        break

        # Check if any deduction depends on the sdr variable
        found_deduction = False
        if 'deductions' in self._price_model:
            for comp in self._price_model['deductions']:
                if 'price_function' not in comp:
                    if sdr['unit'] == comp['unit']:
                        found_deduction = True
                        break
                else:
                    for k, var in comp['price_function']['variables'].iteritems():
                        if var['type'] == 'usage' and var['label'] == sdr['component_label']:
                            found_deduction = True
                            break

        if found_model or found_deduction:
            # Store the SDR
            sdr['time_stamp'] = time_stamp
            self._purchase.contract.pending_sdrs.append(sdr)
        else:
            raise ValueError('The specified unit or component label is not included in the pricing model')

        self._purchase.contract.save()
