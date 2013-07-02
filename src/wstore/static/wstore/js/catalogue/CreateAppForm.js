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

    var makeCreateAppRequest = function makeCreateAppRequest(evnt) {
        var name, version, rep, csrfToken, request = {}, error=false;
        var msg;

        // Stop the hide modal action
        evnt.preventDefault();
        evnt.stopPropagation();

        // Get offering basic info
        name = $.trim($('[name="app-name"]').val());
        version = $.trim($('[name="app-version"]').val());

        if (!name || !version || !logo) {
            error = true;
            msg = 'Missing required field'
        }

        csrfToken = $.cookie('csrftoken');
        request.name = name;
        request.version = version;
        request.image = logo[0];

        // Get usdl info
        if (usdl && ($('#usdl-doc').length > 0)) {
            rep = $('#repositories').val();
            request.offering_description = usdl;
            request.repository = rep;
        } else {
            var usdlLink = $.trim($('#usdl-url').val());

            if (usdlLink) {
                request.description_url = usdlLink;
            } else {
                error = true;
                msg = 'USDL info is missing'
            }
        }

        if (screenShots.length > 0) {
            request.related_images = screenShots;
        }

        // Get notification URL
        if ($('#not-opt-2').prop('checked')) {
            var not_url = $.trim($('#notify').val());
            if (not_url == '') {
                error = true;
                msg = 'Missing notification URL';
            }
            request.notification_url = not_url;
        } else if ($('#not-opt-1').prop('checked')) {
            request.notification_url = 'default';
        } else if (!$('#not-opt-3').prop('checked')) {
            error = true;
            msg = 'Select and option for notification URL';
        }

        if (!error) {
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
        } else {
            MessageManager.showAlertError('Error', msg, $('#error-message'));
        }
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
        $.template('formTemplate', $('#create_app_form_template'));
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

        $('.modal-footer > .btn').click(function(event) {
            makeCreateAppRequest(event);
        });
    };

})();

