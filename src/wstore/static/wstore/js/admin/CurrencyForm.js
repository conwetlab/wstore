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

    var makeCreateCurrencyRequest = function makeCreateCurrencyRequest() {
        var csrfToken = $.cookie('csrftoken');
        var request, msg, error = false;

        var name = $.trim($('#currency-name').val());

        // Check unit name
        if (name == '') {
            error = true;
            msg = "Name field is required";
        }

        // Id the form is correctly filled make the request
        if (!error) {

            // Load data
            request = {
                'currency': name,
            };

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: 'POST',
                url: EndpointManager.getEndpoint('CURRENCY_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    currencyInfoRequest();
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

    var makeDeleteCurencyRequest = function makeDeleteCurrencyRequest(currency) {
        var csrfToken = $.cookie('csrftoken');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: 'DELETE',
            url: EndpointManager.getEndpoint('CURRENCY_ENTRY',  {'currency': currency}),
            dataType: 'json',
            success: function (response) {
                currencyInfoRequest();
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };

    paintCurrencyForm = function paintCurrencyForm () {
        var form;
        $('#admin-container').empty();
        
        $.template('currencyFormTemplate', $('#currency_form_template'));
        $.tmpl('currencyFormTemplate').appendTo('#admin-container');

        // Listener for back link
        $('#back').click(function() {
            if (main) {
                paintElementTable();
            } else {
                currencyInfoRequest();
            }
        });

        // Listener for submit
        $('#currency-submit').click(function() {
            makeCreateCurrencyRequest();
        });
    };

    var paintCurrencies = function paintCurencies(currencies) {
        $('#admin-container').empty();

        if (currencies.allowed_currencies.length > 0) {
            // Create the units list
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'Currencies'}).appendTo('#admin-container');

            // Lister for new unit form
            $('.add').click(function() {
                main = false;
                paintCurrencyForm();
            });

            for (var i = 0; i < currencies.allowed_currencies.length; i++) {
                var row, column, div;

                // Append entry to units table
                $.template('elemTemplate', $('#element_template'));
                row = $.tmpl('elemTemplate', {'name': currencies.allowed_currencies[i]})
                row.appendTo('#table-list');

                row.find('.delete').click((function(curr) {
                    return function() {
                        main = false;
                        makeDeleteCurencyRequest(curr);
                    }
                })(currencies.allowed_currencies[i]));
            }
        } else {
            var msg = 'No currencies registered, you may want to register one'; 
            MessageManager.showAlertInfo('Currency', msg);
        }
        $('#back').click(paintElementTable);
    };

    currencyInfoRequest = function currencyInfoRequest() {
        main = true;

        // Make request asking for the registered currencies
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('CURRENCY_COLLECTION'),
            dataType: "json",
            success: function (response) {
                // Pint units list
                paintCurrencies(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };
})();