# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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


class PriceResolver():

    _applied_sdrs = None

    def __init__(self):
        self._applied_sdrs = {
            'charges': [],
            'deductions': []
        }

    def _price_function_calculation(self, function, variables):
        """
            It calculates the value of a price function
            using the provided function value extracted
            from the different SDR documents
       """
       
        # Get arguments
        if type(function['arg1']) == str or type(function['arg1']) == unicode:
            arg1 = variables[function['arg1']]
        elif type(function['arg1']) == dict:
            arg1 = self._price_function_calculation(function['arg1'], variables)
        else:
            raise Exception('Invalid argument 1')

        if type(function['arg2']) == str or type(function['arg2']) == unicode:
            arg2 = variables[function['arg2']]
        elif type(function['arg2']) == dict:
            arg2 = self._price_function_calculation(function['arg2'], variables)
        else:
            raise Exception('Invalid argument 2')

        result = 0
        # Make operation
        if function['operation'] == '+':
            result = arg1 + arg2
        elif function['operation'] == '-':
            result = arg1 - arg2
        elif function['operation'] == '*':
            result = arg1 * arg2
        elif function['operation'] == '/':
            result = arg1 / arg2
        else:
            raise Exception('Unsupported operation')

        return result

    def _resolve_price_function(self, function, accounting):
        """
           Aggregates the accounting information in the 
           different variables present in a price function
           in order to calculate the related charging
       """

        function = function['price_function']
        # Map price variables id with SDR documents
        aggregated_accounting_val = {}
        for k, v in function['variables'].iteritems():

            if v['type'] == 'usage':
                aggregated_accounting_val[k] = []

                for sdr in accounting:
                    if sdr['component_label'].lower() == v['label'].lower():
                        aggregated_accounting_val[k].append(sdr)
            else:
                aggregated_accounting_val[k] = float(v['value'])

        # Reduce accounting info to a single value per price variable
        for k in aggregated_accounting_val:
            usage = 0
            # Avoid iterations over constants
            if type(aggregated_accounting_val[k]) == list:
                for value in aggregated_accounting_val[k]:
                    usage += float(value['value'])

                aggregated_accounting_val[k] = usage

        return self._price_function_calculation(function['function'], aggregated_accounting_val)

    def _resolve_pay_per_use_agregation(self, component, accounting):
        """
           Resolves the charging of pay per use component based
           on a fixed use value
       """

        result = 0
        for sdr in accounting:
            # Calculate and aggregate price based on value per consumption
            result += (float(sdr['value']) * float(component['value']))

        return result

    def _pay_per_use_preprocesing(self, use_models, accounting_info, discount=False):
        """
           Process pay-per-use payments and call the corresponding
           price calculator
       """

        price = 0
        for payment in use_models: # TODO check if the payment can be applied
            related_accounting = []
            # Check price function
            if 'price_function' in payment:
                for sdr in accounting_info:
                    # Iterate over price variables
                    for k, var in payment['price_function']['variables'].iteritems():
                        if var['label'].lower() == sdr['component_label'].lower():
                            related_accounting.append(sdr)
                agregator = self._resolve_price_function
            else:
                # Get the related accounting info
                for sdr in accounting_info:
                    if sdr['unit'].lower() == payment['unit'].lower():
                        related_accounting.append(sdr)

                agregator = self._resolve_pay_per_use_agregation

            # Include the applied SDRs
            price += agregator(payment, related_accounting)
            applied_accounting = {
                'model': payment,
                'accounting': related_accounting,
                'price': price
            }
            if discount:
                self._applied_sdrs['deductions'].append(applied_accounting)
            else:
                self._applied_sdrs['charges'].append(applied_accounting)

        return price

    def get_applied_sdr(self):
        """
           Returns the applied sdrs in a pay-per-use
           charging
       """
        return self._applied_sdrs

    def resolve_price(self, pricing_model, accounting_info=None):
        """
           Calculates a price to be charged using a pricing
           model and accounting info.
       """

        price = 0
        # Check the pricing model
        if 'single_payment' in pricing_model:
            for payment in pricing_model['single_payment']:
                price = price + float(payment['value'])

        if 'subscription' in pricing_model:
            for payment in pricing_model['subscription']:
                price = price + float(payment['value'])

        if 'pay_per_use' in pricing_model:
            # Calculate the payment associated with the price component
            price = price + self._pay_per_use_preprocesing(pricing_model['pay_per_use'], accounting_info)

        if 'deductions' in pricing_model:
            # Calculate deductions
            price = price - self._pay_per_use_preprocesing(pricing_model['deductions'], accounting_info, discount=True)

        # If the price is negative i.e too much deductions
        # the value is set to 0
        if price < 0:
            price = 0

        return price
