/*
 * Copyright (c) 2013 - 2015 CoNWeT Lab., Universidad Politécnica de Madrid
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

    var taxAddr;
    var plan;
    var free = true;
    var caller;

    /**
     * Handles help popover click events
     * @param evnt, click event
     */
    var helpHandler = function helpHandler(evnt) {
        var helpId = evnt.target;
        if (!$(helpId).prop('displayed')) {
            $(helpId).popover('show');
            $(helpId).prop('displayed', true);
            $(helpId).addClass('question-sing-sel');
            // Add document even
            event.stopPropagation();
            $(document).click(function() {
                $(helpId).popover('hide');
                $(helpId).prop('displayed', false);
                $(helpId).removeClass('question-sing-sel');
                $(document).unbind('click');
            });
        }
    };

    /**
     * Manages the success callback of the purchase in case a PayPal redirection is needed
     * @param response, Server response
     */
    var onSuccessPayPal = function onSuccessPayPal(response) {
        $('#message').modal('hide');
        // Inform user that is going to be redirected, including the redirection handler
        MessageManager.showYesNoWindow('The payment process will continue in a separate window', function() {
            var newWindow;
            var timer, timer1;

            // Close yes no window
            $('#message').modal('hide');

            // Open Payment tab
            newWindow = window.open(response.redirection_link);

            $(window).focus(function() {
                // Create a modal to lock the store during PayPal request
                MessageManager.showMessage('Payment', 'The Paypal checkout is open in another window');

                $('.modal-footer').empty()

                // Include a cancel button
                $('<input></input>').addClass('btn btn-danger').attr('type', 'button').attr('value', 'Cancel').click(function() {
                    $('#message').modal('hide');
                }).appendTo('.modal-footer');

                // Close PayPal window in case the payment is canceled
                $('#message').on('hidden', function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    newWindow.close();
                    $('#message-container').empty();
                })

                // Check if the PayPal window remains open
                timer = setInterval(function() {
                    if (newWindow.closed) {
                        clearInterval(timer);
                        $('#message').modal('hide');
                        caller.refreshAndUpdateDetailsView();
                    } else if (newWindow.location.host == window.location.host) {
                        clearInterval(timer);
                        $('#message').modal('hide');
                        MessageManager.showMessage('Payment', 'The PayPal process has finished. The external window will be closed');

                        $('#message').on('hidden', function() {
                            newWindow.close();
                            caller.refreshAndUpdateDetailsView();
                        });
                    }
                }, 1000);
                $(window).off('focus');
            });

            timer1 = setInterval(function() {

                if ($('#back').length > 0) {
                    clearInterval(timer1);
                    // If the function notifyPurchaseEnd is defined means that is a remote purchase
                    try {
                        if (notifyPurchaseEnd && typeof(notifyPurchaseEnd) == 'function') {
                            notifyPurchaseEnd(response);
                        }
                    } catch (e) {
                    }
                }
            }, 500);

        }, 'Payment'); // End of yes-no window handler
    };

    /**
     * Handler the success callback is case a purchase has finished
     * @param response, Server response
     */
    var onSuccessFinish = function onSuccessFinish(offeringElement, response) {
        var timer;
        //Download resources
        $('#message').modal('hide');
        //Refresh offering details view
        offeringElement.updateOfferingInfo(function(offeringInfo) {
            this.update(offeringInfo);
            if ($(window.location).attr('href').indexOf('contracting') == -1) {
                downloadResources(response);
            }
        }.bind(caller));

        timer = setInterval(function() {

            if ($('#back').length > 0) {
                clearInterval(timer);
                // If the function notifyPurchaseEnd is defined means that is a remote purchase
                try {
                    if (notifyPurchaseEnd && typeof(notifyPurchaseEnd) == 'function') {
                        notifyPurchaseEnd(response);
                    }
                } catch (e) {
                }
            }
        }, 500);
    };

    /**
     * Makes the request for purchasing an offering
     * @param offeringElement, Object with the offering to be purchased
     */
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
            'conditions_accepted': true
        }

        // If a tax address has been provided include it to the request
        if (taxAddr) {
            request.tax_address = taxAddr;
        }

        if (plan) {
            request.plan_label = plan;
        }
        request.payment = {};
        // Add payment info
        if (!free) {
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
        } else {
            request.payment.method = 'paypal';
        }

        if (!error) {
            $('#loading').removeClass('hide'); // Loading view when waiting for requests
            $('#loading').css('height', $(window).height() + 'px');
            $('#message').modal('hide');
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken
                },
                type: "POST",
                url: EndpointManager.getEndpoint('PURCHASE_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    $('#loading').addClass('hide');
                    if ('redirection_link' in response) {
                        onSuccessPayPal(response);
                    } else {
                        onSuccessFinish(offeringElement, response);
                    }
                },
                error: function (xhr) {
                    $('#loading').addClass('hide');
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

    /**
     * Downloads offering resources
     * @param data, Offering data
     */
    var downloadResources = function downloadResources(data) {
        // Open a window with the invoice
        window.open(data.bill[0]);

        // Open the download resources modal
        $('#main-action').click();
    };

    /**
     * Displays the form for selecting the payment method
     * @param offeringElement, Offering to be purchased
     */
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

                $('<label></label>').attr('for', 'curr-card').text('Use registered credit card').appendTo('#method-cont');
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

    /**
     * Displays the form for getting the tax address of the customer
     * @param offeringElement, offering to be purchased
     * @param callerObj, Object that creates the form
     */
    showTaxAddressForm = function showTaxAddressForm(offeringElement, callerObj) {
        var nextButton, cancelButton, pricing, action;
        var checked = false;

        caller = callerObj;
        free = true;

        $('.modal-body').empty();

        $('<div></div>').attr('id', 'purchase-error').appendTo('.modal-body');
        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        $('<label></label>').attr('for', 'tax_addr').text('Use registered tax address').appendTo('.modal-body');
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

        // Set listeners
        $('.modal-footer').empty();
        pricing = offeringElement.getPricing()

        // Check if the offering is free in order to avoid the selection of
        // payment method form
        /*
        if (pricing.price_plans && pricing.price_plans.length > 0) {
            var plan = pricing.price_plans[0]
            if (plan.price_components && plan.price_components.length > 0) {
                free = false;
            }
        }*/

        nextButton = $('<button></button>').attr('class', 'btn btn-basic').appendTo('.modal-footer');
        if (!free) {
            nextButton.text('Next');

            action = showPaymentInfoForm;
            // Append cancel button
            cancelButton = $('<button></button>').attr('class', 'btn btn-danger').text('Cancel');
            cancelButton.appendTo('.modal-footer');
            cancelButton.click(function() {
                $('#message').modal('hide');
            });
        } else {
            nextButton.text('Accept');
            action = makePurchaseRequest;
        }

        nextButton.click(function(evt) {
            var error = false;

            evt.preventDefault();
            // Read the tax address and organization owned values in order to make them
            // available to the next window
            if (!$('#tax_addr').prop('checked')) {
                var street, postal, city, province, country;

                street = $.trim($('#street').val());
                postal = $.trim($('#postal').val());
                city = $.trim($('#city').val());
                province = $.trim($('#province').val());
                country = $.trim($('#country').val());

                if (street != '' && postal != '' && city != '' && province != '' && country != '') {
                    taxAddr = {
                        'street': street,
                        'postal': postal,
                        'city': city,
                        'province': province,
                        'country': country
                    };
                } else {
                    error = true;
                }
            }
            if(!error) {
                action(offeringElement);
            } else {
                var msg = 'A tax address must be provided';
                MessageManager.showAlertError('Error', msg, $('#purchase-error'));
            }
        });
    }

    /**
     * Displays the form for accepting the terms and contiditions that apply to
     * the offering
     */
    showTermsAndConditionsForm = function showTermsAndConditionsForm(offeringElement, callerObj) {
        var legal = offeringElement.getLegal();

        $.template('termsTemplate', $('#terms_and_conditions_template'));
        $.tmpl('termsTemplate').appendTo('.modal-body');

        // Fill legal info
        $('<h3></h3>').text(offeringElement.getLegal().title).appendTo('.conditions-container');

        var text = $('<p></p>').text(offeringElement.getLegal().text).appendTo('.conditions-container');
        var repText = text.text().split('\n').join('<br />');
        text[0].innerHTML = repText;

        // Set checkbox listener
        $('#conditions-accepted').change(function() {
            if ($(this).prop('checked')) {
                $('.modal-footer .btn').prop('disabled', false)
            } else {
                $('.modal-footer .btn').prop('disabled', true)
            }
        });

        // Set next listener
        $('.modal-footer').empty();
        $('<input type="button" class="btn btn-basic" data-dismiss="modal" value="Next" disabled></input>').appendTo('.modal-footer');
        $('.modal-footer .btn').click(function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();

            // Add an aditional check for the terms and conditions
            if (!$('#conditions-accepted').prop('checked')) {
                msg = 'You must accept the terms and conditions to acquire this offering';
                MessageManager.showAlertError('Error', msg, $('#purchase-error'));
                $('#purchase-error .alert').removeClass('span8');
            } else {
                showTaxAddressForm(offeringElement, callerObj);
            }
        });
    };

    /**
     * Dsiplays the form for purchasing an offering
     * @param offeringElement, offering to be purchased
     * @param callerObj, Object that creates the form
     */
    purchaseOffering = function purchaseOffering(offeringElement, callerObj) {
        var plans = offeringElement.getPricing().price_plans;
        // Reset plan value
        plan = null;
        // Create the modal
        MessageManager.showMessage('Acquire offering', '');

        // Check if there are multiple pricing models
        if (plans.length > 1) {
            $('<div></div>').attr('id', 'error-message').appendTo('.modal-body');
            $('<div></div>').addClass('space clear').appendTo('.modal-body');

            // Create the form
            var form = $('<form></form>').addClass('form').appendTo('.modal-body');
            var plansContainer = $('<fieldset></fieldset>').appendTo(form);
            var regularPlans = [];
            var devPlan, updatePlan, helpNeeded = false;

            // Classify price plans
            for (var i = 0; i < plans.length; i++) {
                // Check plan for updating
                if (plans[i].label == 'update') {
                    updatePlan = plans[i];
                // Check plan for developers
                } else if (plans[i].label == 'developer') {
                    devPlan = plans[i];
                } else {
                    regularPlans.push(plans[i]);
                }
            }
            // Append price plans
            $.template('radioPlanTemplate', $('#radio_plan_template'));
            $.tmpl('radioPlanTemplate', regularPlans).appendTo(plansContainer);

            // Append update plan if exists
            if (updatePlan) {
                $.template('radioPlanHelpTemplate', $('#radio_plan_help_template'));
                $.tmpl('radioPlanHelpTemplate', {
                    'type': 'Update',
                    'title': updatePlan.title,
                    'label': 'update',
                    'help': 'This Price plan is thought for updating previous versions of the current offering'
                }).appendTo(plansContainer);
                helpNeeded = true;
            }

            // Append developers plan if exists
            if (devPlan) {
                // Check if developer
                $.template('radioPlanHelpTemplate', $('#radio_plan_help_template'));
                $.tmpl('radioPlanHelpTemplate', {
                    'type': 'Developer',
                    'title': devPlan.title,
                    'label': 'developer',
                    'help': 'This Price plan is thought for developers that want to create new offerings using the resources and applications of the current one'
                }).appendTo(plansContainer);
                helpNeeded = true;
            }

            // Add handlers for help messages if needed
            if (helpNeeded) {
                $('.special-plan-help').popover({'trigger': 'manual'})
                    .click(helpHandler);
            }

            $('[name="plan-inp"]').change(function() {
                plan = $(this).val();
            });

            // Create next button and set handler
            $('.modal-footer > .btn').text('Next').click(function(evnt) {

                evnt.preventDefault();
                evnt.stopPropagation();

                if ($('.special-plan-help').prop('displayed')) {

                    $('.special-plan-help').popover('hide')
                        .prop('displayed', false)
                        .removeClass('question-sing-sel');
                    $(document).unbind('click');
                }

                // Check if a plan has been selected
                if (!plan) {
                    MessageManager.showAlertError('Error', 'A price plan is needed', $('#error-message'));
                } else {
                    // Check if terms and conditions has been provided
                    if (offeringElement.getLegal() && !$.isEmptyObject(offeringElement.getLegal())) {
                        $('.modal-body').empty();
                        showTermsAndConditionsForm(offeringElement, callerObj);
                    } else {
                        showTaxAddressForm(offeringElement, callerObj);
                    }
                }
                
            });
        } else {
            // Check if terms and conditions has been provided
            if (offeringElement.getLegal() && !$.isEmptyObject(offeringElement.getLegal())) {
                showTermsAndConditionsForm(offeringElement, callerObj);
            } else {
                showTaxAddressForm(offeringElement, callerObj);
            }
        }
    };

})();
