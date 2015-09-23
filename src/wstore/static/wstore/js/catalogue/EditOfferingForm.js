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
    var logoFailure = false;
    var screenFailure = false;
    var info = {};
    var currs;
    var currUnits;
    var pricingEditor;

    var fillErrorMessage = function fillErrorMessage(msg, errElems, errContainer) {
        var errorContainer = $('#error-message');

        if (errContainer) {
            errorContainer = errContainer;
        }

        for (var i = 0; i < errElems.length; i++) {
            errElems[i].parent().parent().addClass('error');
        }
        MessageManager.showAlertError('Error', '', errorContainer);
        // Build message content
        $('.alert-error').append(msg[0]);
        for (var i = 1; i < msg.length; i++) {
            $('.alert-error').append('<br>');
            $('.alert-error').append(msg[i]);
        }
        $('.alert-error').removeClass('span8');
        $('.alert-error').bind('closed', function() {
            $('.error').removeClass('error');
        })
    }

    var setVisited = function setVisited(elem) {
        if (!elem.hasClass('.visited')) {
            elem.addClass('visited');
        }
    };

    var getPricingUnits = function (currencies, offeringElement, callerObj) {
        if (!$('#offering-creation-pricing').length) {
            currs = currencies;
            var client = new ServerClient('', 'UNIT_COLLECTION');
            client.get(function(units) {
                displayPricingEditor(units, offeringElement, callerObj)
            });
        } else {
            displayPricingEditor([], offeringElement, callerObj);
        }
    };

    var getAllowedCurrencies = function (offeringElement, callerObj) {
        if (!$('#offering-creation-pricing').length) {
            var client = new ServerClient('', 'CURRENCY_COLLECTION');
            client.get(function(data) {
                getPricingUnits(data, offeringElement, callerObj);
            });
        } else {
            getPricingUnits([], offeringElement, callerObj);
        }
    };

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

        // Preview the image if is the logo
        if (type == 'logo') {
            var prevReader = new FileReader();
            prevReader.readAsDataURL(files[0]);
            prevReader.onloadend = function () {
                $('.image-preview').attr('src', this.result);
            }
        }

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

            var endpoint = EndpointManager.getEndpoint('OFFERING_ENTRY', {
                'name' : offeringElement.getName(),
                'organization': offeringElement.getOrganization(),
                'version': offeringElement.getVersion()
            });

            $('#loading').removeClass('hide');  // Loading view when waiting for requests
            $('#loading').css('height', $(window).height() + 'px');
            $('#message').modal('hide');
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "PUT",
                url: endpoint,
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(info),
                success: function (response) {
                    $('#loading').addClass('hide');
                    $('#message').modal('hide');
                    MessageManager.showMessage('Updated', 'The offering has been updated')
                    caller.refreshAndUpdateDetailsView();
                },
                error: function (xhr) {
                    $('#loading').addClass('hide');
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
    };


    var displayPricingEditor = function (units, offeringElement, callerObj) {
        var footBtn, backBtn;

        // Set navigation button
        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-3').addClass('selected');
        setVisited($('#off-nav-3'));

        if (!$('#offering-creation-pricing').length) {
            currUnits = units;
            pricingEditor = new PricingEditor($('.modal-body'), currUnits, currs);
            pricingEditor.setPricing(offeringElement.getPricing());
            pricingEditor.createListeners();
        } else {
            $('#offering-creation-pricing').removeClass('hide');
        }

        $('.modal-footer').empty();
        backBtn = $('<input class="btn btn-basic" type="button" value="Back"></input>').appendTo('.modal-footer');
        backBtn.click(function(evnt) {
            $('#offering-creation-pricing').addClass('hide');
            showEditDescription(offeringElement, callerObj);
        });

        footBtn = $('<input class="btn btn-blue" type="button" value="Accept"></input>').appendTo('.modal-footer');
        footBtn.click(function(){
            info.offering_description.pricing = pricingEditor.getPricing();
            $('#offering-creation-pricing').addClass('hide');
            makeEditRequest(offeringElement);
        });
    };

    var showEditDescription = function (offeringElement, callerObj) {
        var footBtn, backBtn;

        // Set navigation button
        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-2').addClass('selected');
        setVisited($('#off-nav-2'));

        // Create the form
        if (!$('#offering-creation-usdl').length) {
            $.template('usdlTemplate', $('#select_usdl_form_template'));
            $.tmpl('usdlTemplate').appendTo('.modal-body');
            $('#description').val(offeringElement.getDescription());
            $('#abstract').val(offeringElement.getShortDescription());

            try {
                var legal = offeringElement.getLegal();
                $('#legal-title').val(legal.title);
                $('#legal-text').val(legal.text);
            } catch (err){
            }
        } else {
            $('#offering-creation-usdl').removeClass('hide');
        }
        
        // Listener for application selection
        $('.modal-footer').empty();

        backBtn = $('<input class="btn btn-basic" type="button" value="Back"></input>').appendTo('.modal-footer');
        backBtn.click(function(evnt) {
            $('#offering-creation-usdl').addClass('hide');
            editOfferingForm(offeringElement, callerObj);
        });

        // Set next action
        footBtn = $('<input></input>').addClass('btn btn-basic').attr('type', 'button').val('Next').appendTo('.modal-footer');
        footBtn.click(function(event) {
            var msg = [];
            var errElems = [];
            var error = false;
            var description, abstract;
            var legal = {};

            event.preventDefault();
            event.stopPropagation();

            // Check provided info
            description = $.trim($('#description').val());
            abstract = $.trim($('#abstract').val());

            if (description == '') {
                error = true;
                msg.push('The description is required');
                errElems.push($('#description'));
            }

            if (abstract == '') {
                error = true;
                msg.push('The abstract is required');
                errElems.push($('#abstract'));
            }

            legal.title = $.trim($('#legal-title').val());
            legal.text = $.trim($('#legal-text').val());

            if (legal.title && !legal.text) {
                error = true;
                msg.push('A legal clause needs both title and text');
            errElems.push($('#legal-text'));
            }
            if (legal.text && !legal.title) {
                error = true;
                msg.push('A legal clause needs both title and text');
                errElems.push($('#legal-title'));
            }
            // Include the info
            info.offering_description = {
                'description': description,
                'abstract': abstract,
            }

            // Include the legal info if conpleted
            if (legal.title && legal.text) {
                info.offering_description.legal = legal
            }

            // If the USDL is loaded go to the final step, application selection
            if (!error) {
                $('#offering-creation-usdl').addClass('hide');
                getAllowedCurrencies(offeringElement, callerObj);
            } else {
                fillErrorMessage(msg, errElems, $('#error-message-usdl'));
            }
        });
    };

    editOfferingForm = function editOfferingForm(offeringElement, callerObj) {

        caller = callerObj;
        logo = [];
        screenShots = [];
        usdl = {};

        // Create the window
        if (!$('#update-basic-info').length) {
            MessageManager.showMessage('Edit', '');

            $.template('editFormTemplate', $('#update_off_form_template'));
            $.tmpl('editFormTemplate', {
                'image_url': offeringElement.getLogo()
            }).appendTo('.modal-body');

        } else {
            $('#update-basic-info').removeClass('hide');
        }

        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-1').addClass('selected');
        setVisited($('#off-nav-1'));

        // Set listeners
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

        $('.modal-footer').empty();

        var footBtn = $('<input></input>').addClass('btn btn-basic').attr('type', 'button').val('Next').appendTo('.modal-footer');

        footBtn.click(function(evnt) {
            error = false;
            errElems = [];
            var msg = [];

            evnt.preventDefault();
            evnt.stopPropagation();
            // Check and get new logo
            if (logo.length > 0) {
                info.image = logo[0];
                provided = true;
            }

            // Check and get new screenshots
            if (screenShots.length > 0) {
                info.related_images = screenShots;
                provided = true;
            }

            // Check failures in image loading
            if (logoFailure) {
                error = true;
                msg.push('The provided logo is not valid: Unsupported character in file name');
            }

            // Check failures in image loading
            if (screenFailure) {
                error = true;
                msg.push('Invalid screenshot(s): Unsupported character in file name');
            }

            if ($('#not-opt-2').prop('checked')) {
                var not_url = $.trim($('#notify').val());
                if (not_url == '') {
                    error = true;
                    msg.push('Missing notification URL');
                }
                var nameReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
                if (!nameReg.test(not_url)) {
                    error = true;

                    msg.push('Invalid notification URL format');
                } else {
                    info.notification_url = not_url;
                }
            } else if ($('#not-opt-1').prop('checked')) {
                info.notification_url = 'default';
            }

            if (!error) {
                $('#update-basic-info').addClass('hide');
                showEditDescription(offeringElement);
            } else {
                fillErrorMessage(msg, errElems, $('#update-basic-err'));
            }
        })
    };
})();
