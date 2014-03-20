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
    var logo = [];
    var screenShots = [];
    var usdl = {};
    var caller;

    var handleImageFileSelection = function handleImageFileSelection(evnt, type) {
        var files = evnt.target.files;
        logo = [];
        screenShots = [];

        var imagesList = [];

        var reader = new FileReader();

        var readImages = function readImages(images) {

            if(images.length > 0) {
                var img = images.pop();

                if (img.type.match('image.*')) {
                    reader.onload = (function(file) {

                        return function(e) {
                            var binaryContent = e.target.result;
                            var encoded = btoa(binaryContent);
                            if (type == 'screenshots') {
                                screenShots.push({
                                    'name': file.name,
                                    'data': encoded
                                });
                            } else if (type == 'logo') {
                                logo.push({
                                    'name': file.name,
                                    'data': encoded
                                });
                            }
                            readImages(images);
                        };
                    })(img);
                    reader.readAsBinaryString(img);
                }
            }
        }
        for(var i=0, f; f = files[i]; i+=1){
            imagesList.push(f);
        }
        readImages(imagesList);
    };

    var handleUSDLFileSelection = function handleUSDLFileSelection(evnt) {
        var f = evnt.target.files[0];
        var reader = new FileReader();

        usdl = {};
        reader.onload = (function(file) {
            return function(e) {
                var type = file.type;
                if (!type) {
                    if (file.name.match(/\.n3/i)) {
                        type = "text/n3";
                    } else if (file.name.match(/\.ttl/i)) {
                        type = "text/turtle";
                    }

                }
                if (type == 'application/rdf+xml' || type == 'text/n3' || type == 'text/turtle') {
                    usdl = {
                        'content_type': type,
                        'data': e.target.result
                    };
                }
            };
        })(f);
        reader.readAsText(f);
    };

    var helpHandler = function helpHandler(evnt) {
        var helpId = evnt.target;
        if (!$(helpId).prop('displayed')) {
            $(helpId).popover('show');
            $(helpId).prop('displayed', true);
            $(helpId).addClass('question-sing-sel');
            // Add document even
            evnt.stopPropagation();
            $(document).click(function() {
                $(helpId).popover('hide');
                $(helpId).prop('displayed', false);
                $(helpId).removeClass('question-sing-sel');
                $(document).unbind('click');
            });
        }
    };

    var makeEditRequest = function makeEditRequest(offeringElement) {
        var csrfToken = $.cookie('csrftoken');
        var msg, request = {};
        var provided = false, error = false;

        // Check and get new logo
        if (logo.length > 0) {
            request.image = logo[0];
            provided = true;
        }

        // Check and get new screenshots
        if (screenShots.length > 0) {
            request.related_images = screenShots;
            provided = true;
        }

        // Check and get new USDL description
        if ($('#usdl-doc').length > 0) {
            if (usdl.data && usdl.content_type) {
                request.offering_description = usdl;
                provided = true;
            }
        } else if($('#price-input').length > 0) {

            var description;
            var pricing = {};
            var legal = {};
            var rep = $('#repositories').val();
            // Check provided info
            description = $.trim($('#description').val());

            if (description == '') {
                error = true;
                msg = 'The description is required';
            }
            pricing.price_model = $('#pricing-select').val();

            // If a payment model is selected the price is required
            if (pricing.price_model == 'single_payment') {
                var price = $.trim($('#price-input').val());
                if (price == '') {
                    error = true;
                    msg = 'The price is required for a single payment model';
                } else if (!$.isNumeric(price)){
                    error = true;
                    msg = 'The price must be a number';
                } else {
                    pricing.price = price;
                }
            }
            legal.title = $.trim($('#legal-title').val());
            legal.text = $.trim($('#legal-text').val());

            // Include the info
            request.offering_info = {
                'description': description,
                'pricing': pricing
            }
            // Include the legal info if completed
            if (legal.title && legal.text) {
                request.offering_info.legal = legal
            }
            provided = true

        } else if($('#usdl-url').length > 0){
            var usdlLink = $.trim($('#usdl-url').val());

            if (usdlLink == '') {
                error = true;
                msg = 'Missing USDL Link';

            } else {
                request.description_url = usdlLink;
                provided = true;
            }
        }

        if (!provided) {
            error = true
            msg = 'Not information provided';
        }

        if (!error) {
            var endpoint = EndpointManager.getEndpoint('OFFERING_ENTRY', {
                'name' : offeringElement.getName(),
                'organization': offeringElement.getOrganization(),
                'version': offeringElement.getVersion()
            });

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "PUT",
                url: endpoint,
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    $('#message').modal('hide');
                    MessageManager.showMessage('Updated', 'The offering has been updated')
                    caller.refreshAndUpdateDetailsView();
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showAlertError('Error', msg, $('#edit-error'));
        }
    };

    var displayUploadUSDLForm = function displayUploadUSDLForm() {
        var i;
        var helpMsg = "Upload an USDL document containing the offering info";
        $('#warning-container').empty();

        $('#upload-help').attr('data-content', helpMsg);

        $('#usdl-container').empty();
        $.template('usdlFormTemplate', $('#upload_usdl_form_template'));
        $.tmpl('usdlFormTemplate', {}).appendTo('#usdl-container');

        $('#repositories').remove();
        $('label:contains(Select the repository)').remove();

        $('#usdl-editor').click(function(event) {
            window.open(USDLEDITOR, 'USDL editor');
        });

        $('#usdl-doc').change(function(event) {
            handleUSDLFileSelection(event);
        });
    };

    var displayUSDLLinkForm = function displayUSDLLinkForm() {
        var helpMsg = "Provide an URL of an USDL document uploaded in a Repository";
        $('#warning-container').empty();

        $('#upload-help').attr('data-content', helpMsg);
        $('#usdl-container').empty();
        $('<input></input>').attr('type', 'text').attr('id', 'usdl-url').attr('placeholder', 'USDL URL').appendTo('#usdl-container');
    };

    var checkBasicUSDL = function checkBasicUSDL(offeringElement) {
        var basic = true;
        var pricing = offeringElement.getPricing();
        var legal = offeringElement.getLegal();

        if (legal.length > 0) {
            legal = legal[0];
        }

        $('#description').val(offeringElement.getDescription());
        // Check Pricing model
        if (pricing.price_plans && pricing.price_plans.length > 0) {
            var plan = pricing.price_plans[0];
            if (plan.price_components && plan.price_components.length > 1) {
                basic = false;
            } else if (plan.price_components && plan.price_component.length == 1) {
                var comp = plan.price_components[0];
                if (comp.unit.toLowerCase() == 'single payment') {
                    // Fill the form info
                    $('#pricing-select').val('single_payment');
                    $('#price-input').val(comp.value);
                    $('#price-input').attr('disabled', false);
                } else {
                    basic = false;
                }
            }
        }
        
        // Check Legal conditions
        if (legal.clauses && legal.clauses.length > 0) {
            if (legal.clauses.length == 1) {
                var clause = legal.clauses[0];
                // Fill form info
                $('#legal-title').val(clause.name);
                $('#legal-text').val(clause.text);
            } else {
                basic = false;
            }
        }
        return basic;
    };

    var displayUpdateUSDLInfo = function displayUpdateUSDLInfo(offeringElement) {
        var helpMsg = "Update manually your basic USDL info. This method only supports free or single payment as price models";
        $('#warning-container').empty();

        $('#upload-help').attr('data-content', helpMsg);
        $('#usdl-container').empty();
        $.template('usdlFormTemplate', $('#create_usdl_form_template'));
        $.tmpl('usdlFormTemplate', {}).appendTo('#usdl-container');

        // Remove unecesary inputs
        $('label:contains(Select the repository)').remove();
        $('#repositories').remove();

        if (!checkBasicUSDL(offeringElement)) {
            var msg = 'This offering contains a complex USDL. If you use this method the USDL will be overridden and you may lose some info';
            MessageManager.showAlertWarnig('Warning', msg, $('#warning-container'));
        }

        // Set listeners
        $('#pricing-select').change(function() {
            if ($(this).val() == 'free') {
                $('#price-input').prop('disabled', true);
            } else {
                $('#price-input').prop('disabled', false);
            }
        });
    };
    editOfferingForm = function editOfferingForm(offeringElement, callerObj) {

        caller = callerObj;
        logo = [];
        screenShots = [];
        usdl = {};

        // Create the window
        MessageManager.showMessage('Edit', '');

        $('<div></div>').attr('id', 'edit-error').appendTo('.modal-body');
        $('<div></div>').addClass('clear space').appendTo('.modal-body');

        $.template('editFormTemplate', $('#create_app_form_template'));
        $.tmpl('editFormTemplate').appendTo('.modal-body');

        // Remove unnecessary inputs
        $('[name="app-name"]').remove();
        $('[name="app-version"]').remove();
        $('label:contains(Name)').remove();
        $('label:contains(Version)').remove();

        // Set listeners
        $('#img-logo').change(function(event) {
            handleImageFileSelection(event, 'logo');
        });

        $('#screen-shots').change(function(event) {
            handleImageFileSelection(event, 'screenshots');
        });

        $('#usdl-sel').change(function() {
            if($(this).val() == "1") {
                displayUpdateUSDLInfo(offeringElement);
            } else if($(this).val() == "2") {
                displayUploadUSDLForm();
            } else if ($(this).val() == "3") {
                displayUSDLLinkForm();
            } else {
                var helpMsg = "Select the method to provide the USDL with the new info. You can provide an USDL or provide an URL pointing to an USDL. You can also manually update the info, if you created a basic USDL when you created the offering.";
                $('#upload-help').attr('data-content', helpMsg);
                $('#warning-container').empty();
                $('#usdl-container').empty()
            }
            // Quit the help menu if needed
            if ($('#upload-help').prop('displayed')) {
                $('#upload-help').popover('hide');
                $('#upload-help').prop('displayed', false);
                $('#upload-help').removeClass('question-sing-sel');
            }
        });

        $('#upload-help').popover({'trigger': 'manual'});
        $('#upload-help').click(helpHandler);
        $('#message').on('hide', function() {
            $(document).unbind('click');
            $('.popover').remove();
        });

        $('.modal-footer > .btn').click(function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            makeEditRequest(offeringElement);
        })
    };
})();