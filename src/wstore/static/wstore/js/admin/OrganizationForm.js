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

    var makeCreateOrganizatonRequest = function makeCreateOrganizationRequest(endpoint, method) {
        var request = {}
        var error = false;
        var msg, filled = 0, inputs = 0;

        request.name = $.trim($('#org-name').val());
        request.notification_url = $.trim($('#notify-url').val());

        // Get the tax address
        $('.addr-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            inputs += 1;
        });

        // The tax address is not required; however, if it is wanted to
        // provide it all fields are required.
        if (filled != 0 && filled == inputs) {
            var taxAddr = {
                'street': $.trim($('#street').val()),
                'postal': $.trim($('#postal').val()),
                'city': $.trim($('#city').val()),
                'country': $.trim($('#country').val())
            }
            request.tax_address = taxAddr;
        } else if (filled != 0) {
            error = true;
            msg = 'To provide a tax address all fields are required';
        }

        filled = 0;
        inputs = 0;
        // The credit card info is not required; however, if it is wanted to
        // provide it all fields are required.
        $('.credit-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            inputs += 1;
        });

        if (filled != 0 && filled == inputs && $('#type').val() != 0 && $('#expire-month').val() != 0) {
            var creditCard = {
                'type': $('#type').val(),
                'number': $.trim($('#number').val()),
                'expire_month': $('#expire-month').val(),
                'expire_year': $.trim($('#expire-year').val()),
                'cvv2': $.trim($('#cvv2').val())
            }
            request.payment_info = creditCard;
        } else if (filled != 0) {
            error = true;
            msg = 'To provide a credit card all fields are required';
        }

        if (!error) {
            var csrfToken = $.cookie('csrftoken');

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: method,
                url: endpoint,
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    main = true; 
                    orgInfoRequest(paintOrganizations);
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showMessage('Error', msg);
        }
    }

    paintOrganizations = function paintOrganizations(orgs) {
        $('#admin-container').empty();

        if (orgs.length > 0) {
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'Organizations'}).appendTo('#admin-container');

            for (var i = 0; i < orgs.length; i++) {
                var row, column, div;
                $.template('elemTemplate', $('#element_template'));
                row = $.tmpl('elemTemplate', {'name': orgs[i].name})
                row.appendTo('#table-list');

                column = $('<td></td>');
                div = $('<div></div>').addClass('update').appendTo(column);
                $('<i></i>').addClass('icon-edit').appendTo(div);
                column.appendTo(row);

                div.click((function(org) {
                    return function() {
                        main = false
                        paintOrganizationForm(org);
                    }
                })(orgs[i]));

            }
            $('.add').click(function() {
                main = false;
                paintOrganizationForm();
            })
        } else {
            var msg = 'No organizations registered, you may want to register one'; 
            MessageManager.showAlertInfo('Organizations', msg);
        }
        $('#back').click(paintElementTable);
    }
    
    orgInfoRequest = function orgInfoRequest(callback, arg) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('ORGANIZATION_COLLECTION'),
            dataType: "json",
            success: function (response) {
                if (!arg) {
                    callback(response);
                } else {
                    callback(response, arg);
                }
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    }

    var fillOrganizationForm = function fillOrganizationForm(org) {

        $('#org-name').val(org.name).prop('readonly', true);
        $('#notify-url').val(org.notification_url);

        if (org.payment_info) {
            credit_card = org.payment_info
            $('#type').val(credit_card.type);
            $('#number').val(credit_card.number);
            $('#expire-month').val(credit_card.expire_month);
            $('#expire-year').val(credit_card.expire_year);
            $('#cvv2').val(credit_card.cvv2);
        }

        if (org.tax_address) {
            tax_address = org.tax_address;
            $('#street').val(tax_address.street);
            $('#postal').val(tax_address.postal);
            $('#city').val(tax_address.city);
            $('#country').val(tax_address.country);
        }
        $('#org-submit').text('Update');
    };

    var paintCompleteOrganizationForm = function paintCompleteOrganizationForm(org) {
        var form;

        $('#admin-container').empty();

        // Create the form
        $.template('orgFormTemplate', $('#organization_form_template'));
        $.tmpl('orgFormTemplate').appendTo('#admin-container');

        // Set listeners
        $('#org-submit').click(function() {
            if (org) {
                makeCreateOrganizatonRequest(EndpointManager.getEndpoint('ORGANIZATION_ENTRY', {'org': org.name}), 'PUT');
            } else {
                makeCreateOrganizatonRequest(EndpointManager.getEndpoint('ORGANIZATION_COLLECTION'), 'POST');
            }
        });

        $('#back').click(function() {
            if (main) {
                paintElementTable();
            } else {
                orgInfoRequest(paintOrganizations);
                main = true;
            }
        })
    };

    paintOrganizationForm = function paintOraganizationForm(org) {

        if (org) {
            paintCompleteOrganizationForm(org);
            fillOrganizationForm(org);
        } else {
            paintCompleteOrganizationForm();
        }
    }
})();