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

    var main = true;

    var makeCreateUnitRequest = function makeCreateUnitRequest() {
        var csrfToken = $.cookie('csrftoken');
        var request, msg, error = false;

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

        // Id the form is correctly filled make the request
        if (!error) {

            // Load data
            request = {
                'name': name,
                'defined_model': model
            };

            // Add the renovation period if needed
            if (model == 'subscription') {
                request.renovation_period = $.trim($('#ren-period').val());
            }

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: 'POST',
                url: EndpointManager.getEndpoint('UNIT_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    unitsInfoRequest();
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            })
        } else {
            MessageManager.showMessage('Error', msg);
        }
    };

    paintUnitForm = function paintUnitForm () {
        $('#admin-container').empty();

        $.template('unitFormTemplate', $('#unit_form_template'));
        $.tmpl('unitFormTemplate').appendTo('#admin-container');

        // Listener for back link
        $('#back').click(function() {
            if (main) {
                paintElementTable();
            } else {
                unitsInfoRequest();
            }
        });

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

        // Listener for submit
        $('#unit-submit').click(function() {
            makeCreateUnitRequest();
        });
    };

    var paintUnits = function paintUnits(units) {
        $('#admin-container').empty();

        if (units.length > 0) {
            // Create the units list
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'Units'}).appendTo('#admin-container');

            // Lister for new unit form
            $('.add').click(function() {
                main = false;
                paintUnitForm();
            });

            for (var i = 0; i < units.length; i++) {
                var row, column, div;

                // Append entry to units table
                $.template('elemTemplate', $('#element_template'));
                row = $.tmpl('elemTemplate', {'name': units[i].name, 'host': units[i].defined_model})
                row.appendTo('#table-list');
            }
        } else {
            var msg = 'No units registered, you may want to register one'; 
            MessageManager.showAlertInfo('Units', msg);
        }
        $('#back').click(paintElementTable);
    };

    unitsInfoRequest = function unitsInfoRequest() {
        main = true;

        // Make request asking for the registered units
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('UNIT_COLLECTION'),
            dataType: "json",
            success: function (response) {
                // Pint units list
                paintUnits(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };

})();