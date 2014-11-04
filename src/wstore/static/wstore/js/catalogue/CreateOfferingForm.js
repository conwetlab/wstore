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

    CreateOfferingForm = function CreateOfferingForm() {
        this.screenShots = [];
        this.usdl = null;
        this.logo = [];
        this.offeringInfo = {};
        this.logoFailure = false;
        this.screenFailure = false;
    }

    CreateOfferingForm.prototype = new ModalForm('Create new offering', '#create_off_form_template');

    CreateOfferingForm.prototype.constructor = CreateOfferingForm;

    /**
     * Handles the selection of images, including the validation and
     * encoding
     * @param evnt Event thrown by the file input
     * @param type Type of image (Logo or screenshot)
     */
    var handleImageFileSelection = function handleImageFileSelection(self, evnt, type) {
        var files = evnt.target.files;
        var imagesList = [];

        if (type == 'screenshots') {
            self.screenShots = [];
            self.screenFailure = false;
        } else {
            self.logoFailure = false;
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
                    reader.onload = (function(self, file) {

                        return function(e) {
                            var binaryContent = e.target.result;
                            var encoded = btoa(binaryContent);
                            var imgReg = new RegExp(/^[\w\s-]+\.[\w]+$/);

                            if (type == 'screenshots') {
                                if (!imgReg.test(file.name)) {
                                    self.screenFailure = true;
                                } else {
                                    self.screenShots.push({
                                        'name': file.name,
                                        'data': encoded
                                    });
                                }
                            } else if (type == 'logo') {
                                if (!imgReg.test(file.name)) {
                                    self.logoFailure = true;
                                } else {
                                    self.logo = [{
                                        'name': file.name,
                                        'data': encoded
                                    }];
                                }
                            }
                            if (!self.screenFailure && !self.logoFailure) {
                                readImages(images);
                            }
                        };
                    })(this, img);
                    reader.readAsBinaryString(img);
                }
            }
        }.bind(self);
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

        reader.onload = (function(self, file) {
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
                    this.usdl = {
                        'content_type': type,
                        'data': e.target.result
                    };
                }
            }.bind(self);
        })(this, f);
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
    CreateOfferingForm.prototype.makeCreateOfferingRequest = function makeCreateOfferingRequest(evnt) {
        var csrfToken = $.cookie('csrftoken');
        this.offeringInfo.image = this.logo[0];

        if (this.screenShots.length > 0) {
            this.offeringInfo.related_images = this.screenShots;
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
            data: JSON.stringify(this.offeringInfo),
            success: function (response) {
                $('#loading').addClass('hide');
                var msg = 'Your offering has been created. You have to publish your offering before making it available to third parties.';
                $('#message').modal('hide');
                MessageManager.showMessage('Created', msg);
                if (getCurrentView() == 'provided') {
                    paintCatalogue(true);
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
    };

    /**
     * Displays the form for uploading a USDL document
     */
    CreateOfferingForm.prototype.displayUploadUSDLForm = function displayUploadUSDLForm(repositories) {
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

        $('#usdl-doc').change(handleUSDLFileSelection.bind(this));
    };

    /**
     * Displays the form for providing a URL pointing to an USDL
     */
    CreateOfferingForm.prototype.displayUSDLLinkForm = function displayUSDLLinkForm() {
        var helpMsg = "Provide an URL of an USDL document uploaded in a Repository";
        var cg, ctrls;

        $('#upload-help').attr('data-content', helpMsg);
        $('#usdl-container').empty();
        cg = $('<div class="control-group"></div>').appendTo('#usdl-container')
        $('<label></label>').text('USDL URL*').appendTo(cg);
        ctrls = $('<div class="controls"></div>').appendTo(cg);
        $('<input></input>').attr('type', 'text').attr('id', 'usdl-url').attr('placeholder', 'USDL URL').appendTo(ctrls);
    };

    /**
     * Displays the form for creating a simple USDL document
     */
    CreateOfferingForm.prototype.displayCreateUSDLForm = function displayCreateUSDLForm(repositories) {
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
        if (this.offeringInfo.open) {
            $('#pricing-select').prop('disabled', true);
        } else {
            $('#pricing-select').change(function() {
                if ($(this).val() == 'free') {
                    $('#price-input').prop('disabled', true);
                } else {
                    $('#price-input').prop('disabled', false);
                }
            });
        }
    };

    /**
     * Displays the form for providing the USDL info
     */
    CreateOfferingForm.prototype.showUSDLForm = function showUSDLForm(repositories) {
        var footBtn, backBtn;
        $('.modal-body').empty();

        // Create the form
        $.template('usdlTemplate', $('#select_usdl_form_template'));
        $.tmpl('usdlTemplate').appendTo('.modal-body');

        // If the offering is an open offering show an informative message
        if (this.offeringInfo.open) {
            var msg = 'You are creating an open offering, so you cannot specify a pricing model';
            MessageManager.showAlertInfo('Note', msg, $('#error-message'));
            $('#error-message').removeClass('span8');
        }
        // The create USDL form is displayed by default
        this.displayCreateUSDLForm(repositories);

        // Listener for USDL field
        $('#usdl-sel').change(function(self) {
            return function() {
                if($(this).val() == "0") {
                    self.displayCreateUSDLForm(repositories);
                } else if($(this).val() == "1") {
                    self.displayUploadUSDLForm(repositories);
                } else if ($(this).val() == "2") {
                    self.displayUSDLLinkForm();
                } else {
                    $('#usdl-container').empty()
                }
                // Quit the help menu if needed
                if ($('#upload-help').prop('displayed')) {
                    $('#upload-help').popover('hide');
                    $('#upload-help').prop('displayed', false);
                    $('#upload-help').removeClass('question-sing-sel');
                }
            };
        }(this));

        $('#upload-help').popover({'trigger': 'manual'});
        $('#upload-help').click(helpHandler);
        
        // Listener for application selection
        $('.modal-footer').empty();

        // Set next action
        footBtn = $('<input></input>').addClass('btn btn-classic').attr('type', 'button').val('Next').appendTo('.modal-footer');
        footBtn.click(function(event) {
            var msg = [];
            var errElems = [];
            var error = false;

            event.preventDefault();
            event.stopPropagation();

            if ($('#upload-help').prop('displayed')) {
                $('#upload-help').popover('hide');
                $('#upload-help').prop('displayed', false);
                $('#upload-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }
            // Get usdl info
            if (this.usdl && ($('#usdl-doc').length > 0)) {
                var rep = $('#repositories').val();
                this.offeringInfo.offering_description = this.usdl;
                this.offeringInfo.repository = rep;
            } else if ($('#pricing-select').length > 0) {
                var description;
                var pricing = {};
                var legal = {};
                var rep = $('#repositories').val();
                // Check provided info
                description = $.trim($('#description').val());

                if (description == '') {
                    error = true;
                    msg.push('The description is required');
                    errElems.push($('#description'));
                }
                pricing.price_model = $('#pricing-select').val();

                // If a payment model is selected the price is required
                if (pricing.price_model == 'single_payment') {
                    var price = $.trim($('#price-input').val());
                    if (price == '') {
                        error = true;
                        msg.push('The price is required for a single payment model');
                        errElems.push($('#price-input'));
                    } else if (!$.isNumeric(price)){
                        error = true;
                        msg.push('The price must be a number');
                        errElems.push($('#price-input'));
                    } else {
                        pricing.price = price;
                    }
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
                this.offeringInfo.offering_info = {
                    'description': description,
                    'pricing': pricing
                }
                this.offeringInfo.repository = rep;
                // Include the legal info if conpleted
                if (legal.title && legal.text) {
                    this.offeringInfo.offering_info.legal = legal
                }
            } else {
                var usdlLink = $.trim($('#usdl-url').val());

                if (usdlLink) {
                    // Check link format
                    var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
                    if (!urlReg.test(usdlLink)) {
                        error = true;
                        msg.push('Invalid URL format');
                        errElems.push($('#usdl-url'))
                    } else {
                        this.offeringInfo.description_url = usdlLink;
                    }
                } else {
                    error = true;
                    msg.push('USDL info is missing')
                    errElems.push($('#usdl-url'))
                }
            }

            // If the USDL is loaded go to the final step, application selection
            if (!error) {
                userForm = new BindResourcesForm({});
                userForm.getUserResources(this.showResourcesForm.bind(this), this.offeringInfo.open);
            } else {
                fillErrorMessage(msg, errElems);
            }
        }.bind(this));
    };

    /**
     * Displays the form for the selection of resources
     */
    CreateOfferingForm.prototype.showResourcesForm = function showResourcesForm(resources) {
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
                var templ;

                if (res.state != 'deleted') {
                    res.number = i;
                    $.template('resourceTemplate', $('#resource_template'));
                    templ = $.tmpl('resourceTemplate', res).appendTo('#sel-resources').click(function() {
                        var check = $(this).find('input[type="checkbox"]');
                        if (check.prop('checked')) {
                            check.prop('checked', false);
                        } else {
                            check.prop('checked', true);
                        }
                    });
                    templ.find('input[type="checkbox"]').click(function(e) {
                        if ($(this).prop('checked')) {
                            $(this).prop('checked', false);
                        } else {
                            $(this).prop('checked', true);
                        }
                    });
                    templ.find('.label').remove();
                }
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
            this.offeringInfo.resources = resSelected;

            this.makeCreateOfferingRequest();
        }.bind(this)).appendTo('.modal-footer');
    };

    CreateOfferingForm.prototype.includeContents = function includeContents() {
        var repositoryClient = new ServerClient('', 'REPOSITORY_COLLECTION');
        // Get repositories
        repositoryClient.get(this.fillMainInfo.bind(this), {});
    }

    var fillErrorMessage = function fillErrorMessage(msg, errElems) {
        for (var i = 0; i < errElems.length; i++) {
            errElems[i].parent().parent().addClass('error');
        }
        MessageManager.showAlertError('Error', '', $('#error-message'));
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

    var typeCheckHandler = function typeCheckHandler(regex, errMsg, container) {
        var name = $.trim(container.val());
        var nameReg = new RegExp(regex);
        if (name && !nameReg.test(name)) {
            error = true;

            msg = [errMsg];
            errElems = [container];
            fillErrorMessage(msg, errElems);
        } else {
            container.parent().parent().removeClass('error');
            $('.alert-error').alert('close');
        }
    }

    var versionCheckHandler = function versionCheckHandler() {
        var inter = setInterval(function() {
            typeCheckHandler(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/, 'Invalid version format', $('[name="app-version"]'));
            $('[name="app-version"]').on('change paste keyup', versionCheckHandler);
            clearInterval(inter);
        }, 300);
        $('[name="app-version"]').off();
    }
    /**
     * Displays the form for providing the basic info of the offering
     */
    CreateOfferingForm.prototype.fillMainInfo = function fillMainInfo(repositories) {
        var i, repLength = repositories.length;

        if (repLength == 0) {
            var msg = 'No repositories registered';
            $('.modal-header h2').text('Error');
            $('.modal-body').empty();
            $('.modal-body').append('<p>' + msg + '</p>');
            return
        }

        // Create the listeners
        $('#img-logo').change(function(event) {
            handleImageFileSelection(this, event, 'logo');
        }.bind(this));

        $('#screen-shots').change(function(event) {
            handleImageFileSelection(this, event, 'screenshots');
        }.bind(this));

        $('#notification-help').popover({'trigger': 'manual'});

        $('#notification-help').click(helpHandler.bind(this));

        $('#open-help').popover({'trigger': 'manual'});
        $('#open-help').click(helpHandler.bind(this));

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

        // Set listeners to check inputs when writing
        $('[name="app-name"]').on('change paste keyup', function() {
            typeCheckHandler(/^[\w\s-]+$/, 'Invalid name format: Unsupported character', $(this));
        });

        $('[name="app-version"]').on('change paste keyup', versionCheckHandler);

        $('.modal-footer > .btn').text('Next');
        $('.modal-footer > .btn').click(function(event) {
            var name, version, errElems = [];
            var msg = [];
            var error = false;

            event.preventDefault();
            event.stopPropagation();

            $('.error').removeClass('error');

            if ($('#notification-help').prop('displayed')) {
                $('#notification-help').popover('hide');
                $('#notification-help').prop('displayed', false);
                $('#notification-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }
            if ($('#open-help').prop('displayed')) {
                $('#open-help').popover('hide');
                $('#open-help').prop('displayed', false);
                $('#open-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }

            // Check if the manadatory fields are properly filled
            name = $.trim($('[name="app-name"]').val());
            version = $.trim($('[name="app-version"]').val());

            if (!name || !version || !this.logo.length) {
                error = true;
                var msgMiss = 'Missing required field(s):';
                if (!name) {
                    msgMiss += ' Name';
                    errElems.push($('[name="app-name"]'));
                }
                if(!version) {
                    msgMiss += ' Version';
                    errElems.push($('[name="app-version"]'));
                }
                if(!this.logo.length) {
                    msgMiss += ' Logo';
                    errElems.push($('#img-logo'));
                    msg.push(msgMiss)
                }
            }

            // Check name format
            if (name) {
                var nameReg = new RegExp(/^[\w\s-]+$/);
                if (!nameReg.test(name)) {
                    error = true;

                    msg.push('Invalid name format: Unsupported character');
                    errElems.push($('[name="app-name"]'));
                }
            }

            // Check version format
            if (version) {
                var versReg = new RegExp(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/);
                if (!versReg.test(version)) {
                    error = true;

                    msg.push('Invalid version format');
                    errElems.push($('[name="app-version"]'));
                }
            }
            // Check failures in image loading
            if (this.logoFailure) {
                error = true;

                msg.push('The provided logo is not valid: Unsupported character in file name');
                errElems.push($('#img-logo'));
            }

            // Check failures in image loading
            if (this.screenFailure) {
                error = true;

                msg.push('Invalid screenshot(s): Unsupported character in file name');
                errElems.push($('#screen-shots'));
            }

            // Get the notification URL
            if ($('#not-opt-2').prop('checked')) {
                var not_url = $.trim($('#notify').val());
                if (not_url == '') {
                    error = true;

                    msg.push('Missing notification URL');
                    errElems.push($('#notify'));
                }
                var nameReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
                if (!nameReg.test(not_url)) {
                    error = true;

                    msg.push('Invalid notification URL format');
                    errElems.push($('#notify'));
                } else {
                    this.offeringInfo.notification_url = not_url;
                }
            } else if ($('#not-opt-1').prop('checked')) {
                this.offeringInfo.notification_url = 'default';
            } else if (!$('#not-opt-3').prop('checked')) {
                error = true;

                msg.push('Select an option for notification URL');
                errElems.push($('.radio'));
            }

            // Check if the offering is an open offering
            this.offeringInfo.open = $('#open-offering').prop('checked');

            // If the fields are properly filled, display the next form
            if (!error) {
                this.offeringInfo.name = name;
                this.offeringInfo.version = version;
                this.showUSDLForm(repositories);
            } else {
                fillErrorMessage(msg, errElems)
            }
        }.bind(this));
    };

})();

