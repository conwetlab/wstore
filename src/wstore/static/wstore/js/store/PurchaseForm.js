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

(function(){

    var taxAddr, orgOwned;

    var makePurchaseRequest = function makePurchaseRequest(offeringElement) {
        var csrfToken = $.cookie('csrftoken');
        var error = false;
        var msg;

        // Load the offering info
        var request = {
            'offering': {
                'organization': offeringElement.getOrganization(),
                'name': offeringElement.getName(),
                'version': offeringElement.getVersion()
            },
            'organization_owned': orgOwned
        }

        // If a tax address has been provided include it to the request
        if (taxAddr) {
            request.tax_address = taxAddr;
        }

        // Add payment info
        request.payment = {};
        if ($('#pay-method').val() == 'credit_card') {
            var cvv2 = $.trim($('#cvv2').val());

            request.payment.method = 'credit_card';

            if (!$('#curr-card').prop('checked')) {
                var number, year;

                number = $.trim($('#number').val());
                year = $.trim($('#expire-year').val());

                if (!(number == '') && !(year == '') && !(cvv2 == '')) {
                    request.payment.credit_card = {
                        'number': number,
                        'type': $('#type').val(),
                        'expire_month': $('#expire-month').val(),
                        'expire_year': year,
                        'cvv2': cvv2
                    }
                } else {
                    error = true;
                    msg = 'Missing required field';
                }
            }
        } else if ($('#pay-method').val() == 'paypal'){
            request.payment.method = 'paypal';
        } else {
            error = true;
            msg = 'Please select a payment method';
        }

        if (!error) {
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "POST",
                url: EndpointManager.getEndpoint('PURCHASE_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    if ('redirection_link' in response) {

                        $('#message').modal('hide');
                        MessageManager.showYesNoWindow('The payment process will continue in a separate window', function() {
                            var newWindow = window.open(response.redirection_link);
                            var timer;

                            // Close yes no window
                            $('#message').modal('hide');

                            // Create a modal to lock the store during PayPal request
                            MessageManager.showMessage('Payment', 'The Paypal checkout is open in another window');

                            $('.modal-footer').empty()

                            $('<input></input>').addClass('btn btn-danger').attr('type', 'button').attr('value', 'Cancel').click(function() {
                                $('#message').modal('hide');
                            }).appendTo('.modal-footer');

                            $('#message').on('hidden', function(event) {
                                event.preventDefault();
                                event.stopPropagation();
                                newWindow.close();
                                $('#message-container').empty();
                            })

                            timer = setInterval(function() {
                                if (newWindow.closed) {
                                    clearInterval(timer);
                                    $('#message').modal('hide');
                                    refreshAndUpdateDetailsView();
                                }
                            }, 1000);

                        }, 'Payment');
                    } else {
                        //Download resources
                        if ($(window.location).attr('href').indexOf('contracting') == -1) {
                            downloadResources(response);
                        }
                        //Refresh offering details view
                        offeringElement.setState('purchased');
                        refreshAndUpdateDetailsView();
                        $('#message').modal('hide');
                    }
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showAlertError('Error', msg, $('#purchase-error'));
        }
    };

    var downloadResources = function downloadResources(data) {
        var resources = data.resources;
        for (var i = 0; i < resources.length; i++) {
            window.open(resources[i]);
        }
        window.open(data.bill[0]);
    };

    var showPaymentInfoForm = function showPaymentInfoForm(offeringElement) {
        var select, acceptButton, cancelButton;
        // Crear modal body
        $('.modal-body').empty();

        $('<div></div>').attr('id', 'purchase-error').appendTo('.modal-body');
        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        // Append select component to choose payment method
        $('<p></p>').text('Payment method').appendTo('.modal-body');
        select = $('<select></select>').attr('id', 'pay-method').appendTo('.modal-body');
        $('<option></option>').text('------').appendTo(select);
        $('<option></option>').val('credit_card').text('Credit card').appendTo(select);
        $('<option></option>').val('paypal').text('Paypal').appendTo(select);

        $('<div></div>').attr('id', 'method-cont').appendTo('.modal-body');
        $('#pay-method').change(function() {
            // In case the payment method were credit card, append credit card form
            if ($('#pay-method').val() == 'credit_card') {
                var checked = false;

                $('<label></label>').attr('for', 'curr-card').text('Use user profile credit card').appendTo('#method-cont');
                $('<input></input>').attr('type', 'checkbox').attr('value', 'curr-card').attr('id', 'curr-card').appendTo('#method-cont');
                $('<div></div>').attr('id', 'card-form').appendTo('#method-cont');

                $.template('CreditCardTemplate', $('#credit_card_template'));
                $.tmpl('CreditCardTemplate', {}).appendTo('#card-form');

                // If the user uses their user profile credit card only the cvv2 code
                // is needed
                $('#curr-card').change(function() {
                    if (checked) {
                        $('#card-form').empty();
                        $.template('CreditCardTemplate', $('#credit_card_template'));
                        $.tmpl('CreditCardTemplate', {}).appendTo('#card-form');
                        checked = false
                    } else {
                        $('#card-form').empty();
                        checked = true;
                    }
                })
            } else {
                $('#method-cont').empty();
            }
        });

        $('.modal-footer').empty();
        acceptButton = $('<button></button>').attr('class', 'btn btn-basic').appendTo('.modal-footer');
        acceptButton.text('Accept');

        acceptButton.click(function(evnt) {
            evnt.preventDefault();
            makePurchaseRequest(offeringElement);
        });

        cancelButton = $('<button></button>').attr('class', 'btn btn-danger').text('Cancel');
        cancelButton.appendTo('.modal-footer');
        cancelButton.click(function() {
            $('#message').modal('hide');
        })
    };

    purchaseOffering = function purchaseOffering(offeringElement) {
        var nextButton, cancelButton;
        var checked = false;

        // Create the modal
        MessageManager.showMessage('Purchase offering', '');

        $('<div></div>').attr('id', 'purchase-error').appendTo('.modal-body');
        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        $('<label></label>').attr('for', 'tax_addr').text('Use user profile tax address').appendTo('.modal-body');
        $('<input></input>').attr('type', 'checkbox').attr('value', 'tax_addr').attr('id', 'tax_addr').appendTo('.modal-body');
        $('<div></div>').attr('id', 'addr_cont').appendTo('.modal-body');

        // Append Tax address form
        $.template('purchaseTemplate', $('#purchase_form_template'));
        $.tmpl('purchaseTemplate', {}).appendTo('#addr_cont');

        // If the user profile tax address is selected the form it is not necessary
        $('#tax_addr').change(function () {
            if(checked) {
                $.template('purchaseTemplate', $('#purchase_form_template'));
                $.tmpl('purchaseTemplate', {}).appendTo('#addr_cont');
                checked = false;
            } else {
                $('#addr_cont').empty();
                checked = true;
            }
        });

        $('<label></label>').attr('for', 'owned').text('Make the offering available to the whole organization').appendTo('.modal-body');
        $('<input></input>').attr('type', 'checkbox').attr('value', 'owned').attr('id', 'owned').appendTo('.modal-body');

        // Set listeners
        $('.modal-footer').empty();
        nextButton = $('<button></button>').attr('class', 'btn btn-basic').appendTo('.modal-footer');
        nextButton.text('Next');

        nextButton.click(function(evt) {
            var error = false;

            evt.preventDefault();
            // Read the tax address and organization owned values in order to make them
            // available to the next window
            if (!$('#tax_addr').prop('checked')) {
                var street, postal, city, country;

                street = $.trim($('#street').val());
                postal = $.trim($('#postal').val());
                city = $.trim($('#city').val());
                country = $.trim($('#country').val());

                if (street != '' && postal != '' && city != '' && country != '') {
                    taxAddr = {
                        'street': street,
                        'postal': postal,
                        'city': city,
                        'country': country
                    };
                } else {
                    error = true;
                }
            }
            if(!error) {
                orgOwned = $('#owned').prop('checked');
                showPaymentInfoForm(offeringElement);
            } else {
                var msg = 'A tax address must be provided';
                MessageManager.showAlertError('Error', msg, $('#purchase-error'));
            }
        });

        // Append cancel button
        cancelButton = $('<button></button>').attr('class', 'btn btn-danger').text('Cancel');
        cancelButton.appendTo('.modal-footer');
        cancelButton.click(function() {
            $('#message').modal('hide');
        })
    };

})();
