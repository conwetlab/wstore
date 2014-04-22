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

(function () {

    var screenShots = [];
    var usdl;
    var logo = [];
    var offeringInfo = {};
    var logoFailure = false;
    var screenFailure = false;

    /**
     * Handles the selection of images, including the validation and
     * encoding
     * @param evnt Event thrown by the file input
     * @param type Type of image (Logo or screenshot)
     */
    var handleImageFileSelection = function handleImageFileSelection(evnt, type) {
        var files = evnt.target.files;
        var imagesList = [];

        if (type == 'screenshots') {
            screenShots = [];
            screenFailure = false;
        } else {
            logoFailure = false;
        }

        var reader = new FileReader();

        var readImages = function readImages(images) {

            if(images.length > 0) {
                var img = images.pop();

                if (img.type.match('image.*')) {
                    reader.onload = (function(file) {

                        return function(e) {
                            var binaryContent = e.target.result;
                            var encoded = btoa(binaryContent);
                            var imgReg = new RegExp(/^[\w\s-]+\.[\w]+$/);

                            if (type == 'screenshots') {
                                if (!imgReg.test(file.name)) {
                                    screenFailure = true;
                                } else {
                                    screenShots.push({
                                        'name': file.name,
                                        'data': encoded
                                    });
                                }
                            } else if (type == 'logo') {
                                if (!imgReg.test(file.name)) {
                                    logoFailure = true;
                                } else {
                                    logo = [{
                                        'name': file.name,
                                        'data': encoded
                                    }];
                                }
                            }
                            if (!screenFailure && !logoFailure) {
                                readImages(images);
                            }
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

    /**
     * Handles the uploading of an USDL document
     * @param evnt Event thrown by the file input
     */
    var handleUSDLFileSelection = function handleUSDLFileSelection(evnt) {
        var f = evnt.target.files[0];
        var reader = new FileReader();

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

    /**
     * Make the request for creating the offering using the provided info
     */
    var makeCreateOfferingRequest = function makeCreateOfferingRequest(evnt) {
        var csrfToken = $.cookie('csrftoken');
        offeringInfo.image = logo[0];

        if (screenShots.length > 0) {
            offeringInfo.related_images = screenShots;
        }

        $('#loading').removeClass('hide');  // Loading view when waiting for requests
        $('#loading').css('height', $(window).height() + 'px');
        $('#message').modal('hide');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "POST",
            url: EndpointManager.getEndpoint('OFFERING_COLLECTION'),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(offeringInfo),
            success: function (response) {
                $('#loading').addClass('hide');
                var msg = 'Your offering has been created. You have to publish your offering before making it available to third parties.';
                MessageManager.showMessage('Created', msg);
                if (getCurrentTab() == '#provided-tab') {
                    getUserOfferings('#provided-tab', paintProvidedOfferings, EndpointManager.getEndpoint('OFFERING_COLLECTION'), false);
                }
            },
            error: function (xhr) {
                $('#loading').addClass('hide');
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    /**
     * Displays the form for uploading a USDL document
     */
    var displayUploadUSDLForm = function displayUploadUSDLForm(repositories) {
        var i, repLength = repositories.length;
        var helpMsg = "Upload an USDL document containing the offering info";

        $('#upload-help').attr('data-content', helpMsg);
        $('#usdl-container').empty();
        $.template('usdlFormTemplate', $('#upload_usdl_form_template'));
        $.tmpl('usdlFormTemplate', {}).appendTo('#usdl-container');

        for(i=0; i<repLength; i+=1) {
            $.template('radioTemplate', $('#radio_template'));
            $.tmpl('radioTemplate', {
                'name': 'rep-radio',
                'id': 'rep-radio' + i,
                'value': repositories[i].name,
                'text': repositories[i].name}).appendTo('#repositories');
        }

        $('#usdl-editor').click(function(event) {
            window.open(USDLEDITOR, 'USDL editor');
        });

        $('#usdl-doc').change(function(event) {
            handleUSDLFileSelection(event);
        });
    };

    /**
     * Displays the form for providing a URL pointing to an USDL
     */
    var displayUSDLLinkForm = function displayUSDLLinkForm() {
        var helpMsg = "Provide an URL of an USDL document uploaded in a Repository";

        $('#upload-help').attr('data-content', helpMsg);
        $('#usdl-container').empty();
        $('<label></label>').text('USDL URL').appendTo('#usdl-container');
        $('<input></input>').attr('type', 'text').attr('id', 'usdl-url').attr('placeholder', 'USDL URL').appendTo('#usdl-container');
    };

    /**
     * Displays the form for creating a simple USDL document
     */
    var displayCreateUSDLForm = function displayCreateUSDLForm(repositories) {
        var i, repLength = repositories.length;
        var helpMsg = "Create a basic USDL for your offering. This method only supports free or single payment as price models";

        $('#upload-help').attr('data-content', helpMsg);
        $('#usdl-container').empty();
        $.template('usdlFormTemplate', $('#create_usdl_form_template'));
        $.tmpl('usdlFormTemplate', {}).appendTo('#usdl-container');

        for(i=0; i<repLength; i+=1) {
            $.template('radioTemplate', $('#radio_template'));
            $.tmpl('radioTemplate', {
                'name': 'rep-radio',
                'id': 'rep-radio' + i,
                'value': repositories[i].name,
                'text': repositories[i].name}).appendTo('#repositories');
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

    /**
     * Displays the form for providing the USDL info
     */
    var showUSDLForm = function showUSDLForm(repositories) {
        var footBtn;
        $('.modal-body').empty();

        // Create the form
        $.template('usdlTemplate', $('#select_usdl_form_template'));
        $.tmpl('usdlTemplate').appendTo('.modal-body');

        // The create USDL form is displayed by default
        displayCreateUSDLForm(repositories);

        // Listener for USDL field
        $('#usdl-sel').change(function() {
            if($(this).val() == "0") {
                displayCreateUSDLForm(repositories);
            } else if($(this).val() == "1") {
                displayUploadUSDLForm(repositories);
            } else if ($(this).val() == "2") {
                displayUSDLLinkForm();
            } else {
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

        // Listener for application selection
        $('.modal-footer').empty();
        footBtn = $('<input></input>').addClass('btn btn-classic').attr('type', 'button').val('Next').appendTo('.modal-footer');
        footBtn.click(function(event) {
            var msg, error = false;

            event.preventDefault();
            event.stopPropagation();

            if ($('#upload-help').prop('displayed')) {
                $('#upload-help').popover('hide');
                $('#upload-help').prop('displayed', false);
                $('#upload-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }
            // Get usdl info
            if (usdl && ($('#usdl-doc').length > 0)) {
                var rep = $('#repositories').val();
                offeringInfo.offering_description = usdl;
                offeringInfo.repository = rep;
            } else if ($('#pricing-select').length > 0) {
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
                offeringInfo.offering_info = {
                    'description': description,
                    'pricing': pricing
                }
                offeringInfo.repository = rep;
                // Include the legal info if conpleted
                if (legal.title && legal.text) {
                    offeringInfo.offering_info.legal = legal
                }
            } else {
                var usdlLink = $.trim($('#usdl-url').val());

                if (usdlLink) {
                    // Check link format
                    var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
                    if (!urlReg.test(usdlLink)) {
                        error = true;
                        msg = 'Invalid URL format';
                    } else {
                        offeringInfo.description_url = usdlLink;
                    }
                } else {
                    error = true;
                    msg = 'USDL info is missing'
                }
            }

            // If the USDL is loaded go to the final step, application selection
            if (!error) {
                var userForm = new BindResourcesForm({});
                userForm.getUserResources(showResourcesForm);
            } else {
                MessageManager.showAlertError('Error', msg, $('#error-message'));
            }
        });
    };

    /**
     * Displays the form for the selection of resources
     */
    var showResourcesForm = function showResourcesForm(resources) {
        $('.modal-body').empty();
        $('.modal-footer').empty()

        $.template('selectResourcesTemplate', $('#resources_form_template'));
        $.tmpl('selectResourcesTemplate').appendTo('.modal-body');

        $('#resources-help').popover({'trigger': 'manual'});
        $('#resources-help').click(helpHandler);
        if (resources.length > 0) {
         // Apend the provider resources
            for (var i = 0; i < resources.length; i++) {
                var res = resources[i];
                var found = false;
                var j = 0;

                res.number = i;
                $.template('resourceTemplate', $('#resource_template'));
                $.tmpl('resourceTemplate', res).appendTo('#sel-resources').on('hover', function(e) {
                    $(e.target).popover('show');
                });
            }
        } else {
            var msg = "You don't have any resource registered. Press accept to create the offering without resources (You can bind resources later, before publishing the offering).";
            MessageManager.showAlertInfo('No Resources', msg, $('#sel-resources'));
        }

        // Append the Accept button
        $('<input></input>').attr('type', 'button').addClass('btn btn-clasic').attr('value', 'Accept').click(function() {
            var resSelected = [];

            if ($('#resources-help').prop('displayed')) {
                $('#resources-help').popover('hide');
                $('#resources-help').prop('displayed', false);
                $('#resources-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }

            for (var i = 0; i < resources.length; i++) {
                if ($('#check-' + i).prop("checked")) {
                    resSelected.push({
                        'name': resources[i].name,
                        'version': resources[i].version
                    })
                }
            }
            offeringInfo.resources = resSelected;

            makeCreateOfferingRequest();
        }).appendTo('.modal-footer');
    };

    /**
     * Displays the form for providing the basic info of the offering
     */
    showCreateAppForm = function showCreateAppForm(repositories) {
        var i, repLength = repositories.length;

        screenShots = [];
        logo = [];

        if (repLength == 0) {
            var msg = 'No repositories registered';
            MessageManager.showMessage('Error', msg);
            return
        }
        // Creates the modal
        MessageManager.showMessage('Create new offering', '');

        // Creates the form
        $.template('formTemplate', $('#create_off_form_template'));
        $.tmpl('formTemplate', {}).appendTo('.modal-body');

        // Create the listeners
        $('#img-logo').change(function(event) {
            handleImageFileSelection(event, 'logo');
        });

        $('#screen-shots').change(function(event) {
            handleImageFileSelection(event, 'screenshots');
        });

        $('#notification-help').popover({'trigger': 'manual'});

        $('#notification-help').click(helpHandler);

        $('[name="notify-select"]').change(function() {
           if ($(this).val() == 'new') {
               $('#notify').removeClass('hide');
           } else {
               $('#notify').addClass('hide');
           }
        });

        // set hidden listener
        $('#message').on('hide', function() {
            $(document).unbind('click');
            $('.popover').remove();
        });

        $('.modal-footer > .btn').text('Next');
        $('.modal-footer > .btn').click(function(event) {
            var name, version;
            var msg, error = false;

            event.preventDefault();
            event.stopPropagation();

            if ($('#notification-help').prop('displayed')) {
                $('#notification-help').popover('hide');
                $('#notification-help').prop('displayed', false);
                $('#notification-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }

            // Check if the manadatory fields are properly filled
            name = $.trim($('[name="app-name"]').val());
            version = $.trim($('[name="app-version"]').val());

            if (!name || !version || !logo.length) {
                error = true;
                msg = 'Missing required field(s):';
                if (!name) {
                    msg += ' Name';
                }
                if(!version) {
                    msg += ' Version';
                }
                if(!logo.length) {
                    msg += ' Logo';
                }
            }

            // Check name format
            if (name) {
                var nameReg = new RegExp(/^[\w\s-]+$/);
                if (!nameReg.test(name)) {
                    error = true;
                    msg = 'Invalid name format: Unsupported character';
                }
            }

            // Check failures in image loading
            if (logoFailure) {
                error = true;
                msg = 'The provided logo is not valid: Unsupported character in file name';
            }

            // Check failures in image loading
            if (screenFailure) {
                error = true;
                msg = 'Invalid screenshot(s): Unsupported character in file name';
            }

            // Get the notification URL
            if ($('#not-opt-2').prop('checked')) {
                var not_url = $.trim($('#notify').val());
                if (not_url == '') {
                    error = true;
                    msg = 'Missing notification URL';
                }
                offeringInfo.notification_url = not_url;
            } else if ($('#not-opt-1').prop('checked')) {
                offeringInfo.notification_url = 'default';
            } else if (!$('#not-opt-3').prop('checked')) {
                error = true;
                msg = 'Select and option for notification URL';
            }

            // If the fields are properly filled, display the next form
            if (!error) {
                offeringInfo.name = name;
                offeringInfo.version = version;
                showUSDLForm(repositories);
            } else {
                MessageManager.showAlertError('Error', msg, $('#error-message'));
            }
        });
    };

})();

