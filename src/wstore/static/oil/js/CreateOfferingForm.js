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

    var handleImageFileSelection = function handleImageFileSelection(evnt, type) {
        var files = evnt.target.files;
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

    var makeCreateOfferingRequest = function makeCreateOfferingRequest(evnt) {
        var csrfToken = $.cookie('csrftoken');
        offeringInfo.image = logo[0];

        if (screenShots.length > 0) {
            offeringInfo.related_images = screenShots;
        }

        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "POST",
            url: EndpointManager.getEndpoint('OFFERING_COLLECTION'),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: function (response) {
                $('#message').modal('hide');
                MessageManager.showMessage('Created', 'The offering has been created')
                if (getCurrentTab() == '#provided-tab') {
                    getUserOfferings('#provided-tab', paintProvidedOfferings, false);
                }
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                $('#message').modal('hide');
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var displayUploadUSDLForm = function displayUploadUSDLForm(repositories) {
        var i, repLength = repositories.length;

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

    var displayUSDLLinkForm = function displayUSDLLinkForm() {
        $('#usdl-container').empty();
        $('<input></input>').attr('type', 'text').attr('id', 'usdl-url').attr('placeholder', 'USDL URL').appendTo('#usdl-container');
    };

    var showUSDLForm = function showUSDLForm(repositories) {
        $('.modal-body').empty();

        // Create the form
        $.template('usdlTemplate', $('#select_usdl_form_template'));
        $.tmpl('usdlTemplate').appendTo('.modal-body');

        // Listener for USDL field
        $('#usdl-sel').change(function() {
            if($(this).val() == "1") {
                displayUploadUSDLForm(repositories);
            } else if ($(this).val() == "2") {
                displayUSDLLinkForm();
            } else {
                $('#usdl-container').empty()
            }
        });

        $('#upload-help').on('hover', function () {
            $('#upload-help').popover('show');
        });

        // Listener for application selection
        $('.modal-footer > .btn').click(function(event) {
            var msg, error = false;

            event.preventDefault();
            event.stopPropagation();

            // Get usdl info
            if (usdl && ($('#usdl-doc').length > 0)) {
                var rep = $('#repositories').val();
                offeringInfo.offering_description = usdl;
                offeringInfo.repository = rep;
            } else {
                var usdlLink = $.trim($('#usdl-url').val());

                if (usdlLink) {
                    offeringInfo.description_url = usdlLink;
                } else {
                    error = true;
                    msg = 'USDL info is missing'
                }
            }

            // If the USDL is loaded go to the final step, application selection
            if (!error) {
                getApplications();
            } else {
                MessageManager.showAlertError('Error', msg, $('#error-message'));
            }
        });
    };

    var getApplications = function getApplications () {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('APPLICATION_COLLECTION'),
            dataType: 'json',
            contentType: 'application/json',
            success: function (response) {
                showApplicationsForm(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showAlertError('Error', msg, $('#error-message'));
            }
        })
    };

    var showApplicationsForm = function showApplicationsForm(applications) {
        $('.modal-body').empty();

        // Create the form
        $.template('offDescTemplate', $('#select_application_form_template'));
        $.tmpl('offDescTemplate').appendTo('.modal-body');

        // Include applications
        $.template('appCheckTemplate', $('#application_select_template'));
        $.tmpl('appCheckTemplate', applications).appendTo('#applications');

        // Set button listener
        $('.modal-footer > .btn').text('Accept');
        $('.modal-footer > .btn').click(function(evnt) {
            var applications = [];
            evnt.preventDefault();
            evnt.stopPropagation();

            // Check tha selected applications
            $('input[type="checkbox"]').each(function() {
                if ($(this).prop('checked')) {
                    applications.push({
                        'name': $(this).attr('name'),
                        'url': $('#' + $(this).attr('id') + '-url').attr('href'),
                        'id': $(this).attr('id')
                    });
                }
            });

            // Make the request
            if (applications.lenght > 0) {
                offeringInfo.applications = applications;
                makeCreateOfferingRequest();
            } else {
                MessageManager.showAlertError('Error', 'No applications selected', $('#error-message'));
            }
        })
    };

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

        $('[name="notify-select"]').change(function() {
           if ($(this).val() == 'new') {
               $('#notify').removeClass('hide');
           } else {
               $('#notify').addClass('hide');
           }
        });

        $('.modal-footer > .btn').text('Next');
        $('.modal-footer > .btn').click(function(event) {
            var name, version;
            var msg, error = false;

            event.preventDefault();
            event.stopPropagation();
            // Check if the manadatory fields are properly filled
            name = $.trim($('[name="app-name"]').val());
            version = $.trim($('[name="app-version"]').val());

            if (!name || !version || !logo) {
                error = true;
                msg = 'Missing required field';
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

