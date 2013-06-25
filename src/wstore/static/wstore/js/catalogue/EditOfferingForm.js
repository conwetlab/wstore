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
        } else {
            var usdlLink = $.trim($('#usdl-url').val());
            var contentType = $.trim($('#content-type').val());

            if (usdlLink != '' && contentType == '') {
                error = true;
                msg = 'Missing content type';
                
            } else if (usdlLink == '' && contentType != '') {
                error = true;
                msg = 'Missing USDL Link';

            } else if (usdlLink != '' && contentType != '') {
                request.description_url = {
                    'link': usdlLink,
                    'content_type': contentType
                }
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
                    MessageManager.showMessage('Created', 'The offering has been updated')
                    refreshAndUpdateDetailsView();
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
        $('#usdl-container').empty();

        $('<input></input>').attr('type', 'text').attr('id', 'content-type').attr('placeholder', 'Content type').appendTo('#usdl-container');
        $('<div></div>').addClass('clear space').appendTo('#usdl-container');
        $('<input></input>').attr('type', 'text').attr('id', 'usdl-url').attr('placeholder', 'USDL URL').appendTo('#usdl-container');
    };

    editOfferingForm = function editOfferingForm(offeringElement) {

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
                displayUploadUSDLForm();
            } else if ($(this).val() == "2") {
                displayUSDLLinkForm();
            } else {
                $('#usdl-container').empty()
            }
        });

        $('#upload-help').on('hover', function () {
            $('#upload-help').popover('show');
        });
        $('.modal-footer > .btn').click(function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            makeEditRequest(offeringElement);
        })
    };
})();