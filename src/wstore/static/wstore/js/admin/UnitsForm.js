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
     * Units Form constructor
     */
    UnitsForm = function UnitsForm() {
    };

    /**
     * Units form is a subclass of AdminForm
     */
    UnitsForm.prototype = new AdminForm('', 'UNIT_COLLECTION', $($('#unit_form_template')));
    UnitsForm.prototype.constructor = UnitsForm;

    /**
     * Implementation of validateFields abstract method, validate
     * Unit form and get form info.
     */
    UnitsForm.prototype.validateFields = function validateFields() {
        var validation = {};
        var msg, error = false;

        var name = $.trim($('#unit-name').val());
        var model = $('#defined-model').val();

        // Check unit name
        if (name == '') {
            error = true;
            msg = "Name field is required";
        }

        // Check renovation period
        if (model == 'subscription') {
            if ($.trim($('#ren-period').val()) == ''){
                error = true;
                msg = 'The reovation period is required';
            }
        }

        validation.valid = !error;
        // Id the form is correctly filled make the request
        if (!error) {
            validation.data = {
                'name': name,
                'defined_model': model
            };

            // Add the renovation period if needed
            if (model == 'subscription') {
                validation.data.renovation_period = $.trim($('#ren-period').val());
            }

        } else {
            validation.msg = msg;
        }
        return validation;
    };

    /**
     * Implementation of setFormListeners abstract method, creates
     * extra listeners included in the form.
     */
    UnitsForm.prototype.setFormListeners = function setFormListeners () {
        // Listener for renovation period
        $('#defined-model').change(function() {
            if ($(this).val() == 'subscription') {
                $('#ren-period').removeClass('hide');
                $('label:contains(Renovation Period)').removeClass('hide');
            } else {
                $('#ren-period').addClass('hide');
                $('label:contains(Renovation Period)').addClass('hide');
            }
        });
    };

    /**
     * Implementation of fillListInfo abstract nethod, includes
     * Units in the list view.
     */
    UnitsForm.prototype.fillListInfo = function fillListInfo(units) {
        for (var i = 0; i < units.length; i++) {
            var row, column, div;

            // Append entry to units table
            $.template('elemTemplate', $('#element_template'));
            row = $.tmpl('elemTemplate', {'name': units[i].name, 'host': units[i].defined_model})
            row.appendTo('#table-list');
        }
    };

})();