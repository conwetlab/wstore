/*
 * Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid
 *
 * This file is part of WStore.
 *
 * WStore is free software: you can redistribute it and/or modify
 * it under the terms of the European Union Public Licence (EUPL)
 * as published by the European Commission, either version 1.1
 * of the License, or (at your option) any later version.
 *
 * WStore is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * European Union Public Licence for more details.
 *
 * You should have received a copy of the European Union Public Licence
 * along with WStore.
 * If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.
 */

(function() {

    /**
     * Currency form constructor
     * @returns {CurrencyForm}
     */
    CurrencyForm = function CurrencyForm() {
    };

    // CurrencyForm is a subclass of AdminForm
    CurrencyForm.prototype = new AdminForm('CURRENCY_ENTRY', 'CURRENCY_COLLECTION', $('#currency_form_template'));
    CurrencyForm.prototype.constructor = CurrencyForm;

    /**
     * Implementation of the abstract method defined in AdminForm
     * @returns Validation result, including the data if OK or the fields
     * with problems if not OK
     */
    CurrencyForm.prototype.validateFields = function validateFields() {
        var validation = {}
        var name = $.trim($('#currency-name').val());

        validation.valid = true;

        // Check unit name
        if (!name) {
            validation.valid = false;
            validation.msg = "Name field is required";
            validation.errFields = [$('#currency-name').parent().parent()];
        } else {
            var nameReg = new RegExp(/^[\w\s-]+$/);
            if (!nameReg.test(name)) {
                validation.valid = false;
                validation.msg =  "Invalid name format";
                validation.errFields = [$('#currency-name').parent().parent()];
            }
        }

        // Id the form is correctly filled return values
        if (validation.valid) {
            validation.data = {
                'currency': name,
                'default': $('#is-default').prop('checked')
            };
        }
        return validation;
    };

    CurrencyForm.prototype.fillListInfo = function fillListInfo(currencies) {
        // Create the template
        $.template('elemTemplate', $('#element_template'));

        for (var i = 0; i < currencies.length; i++) {
            var row, column, div, context, editable = false;

            context = {
                'name': currencies[i].currency
            }

            if (currencies[i].default) {
                context.host = 'default';
            } else {
                editable = true
            }
            row = $.tmpl('elemTemplate', context)
            row.appendTo('#table-list');

            // Set listener for deletion
            row.find('.delete').click((function(self, curr) {
                return function() {
                    var urlContext = {
                        'currency': curr
                    };
                    self.mainClient.remove(self.elementInfoRequest.bind(self), urlContext);
                }
            })(this, currencies[i].currency));

            // Check if it is possible to make the currency default
            if (editable) {
                var elemInfo = row.find('#elem-info');
                $('<i></i>').addClass('icon-edit').appendTo(elemInfo);
                elemInfo.click((function(self, curr) {
                    return function() {
                        var urlContext = {
                            'currency': curr
                        };
                        self.mainClient.update({}, self.elementInfoRequest.bind(self), urlContext);
                    }
                })(this, currencies[i].currency));
            }
        }
    };

    CurrencyForm.prototype.setFormListeners = function setFormListeners() {
    };

})();
