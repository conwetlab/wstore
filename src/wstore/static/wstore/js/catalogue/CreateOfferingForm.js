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

(function () {

    CreateOfferingForm = function CreateOfferingForm() {
        this.screenShots = [];
        this.usdl = null;
        this.logo = [];
        this.offeringInfo = {};
        this.logoFailure = false;
        this.screenFailure = false;
        this.apps = {};
        this.resources = [];
        this.currencies = [];
        this.units = {};
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

    var setVisited = function setVisited(elem) {
        if (!elem.hasClass('.visited')) {
            elem.addClass('visited');
        }
    };

    CreateOfferingForm.prototype.getPricingUnits = function getPricingUnits(currencies) {
        if (!$('#offering-creation-pricing').length) {
            this.currencies = currencies;
            var client = new ServerClient('', 'UNIT_COLLECTION');
            client.get(this.displayPricingEditor.bind(this));
        } else {
            this.displayPricingEditor();
        }
    };

    CreateOfferingForm.prototype.getAllowedCurrencies = function getAllowedCurrencies() {
        if (!$('#offering-creation-pricing').length) {
            var client = new ServerClient('', 'CURRENCY_COLLECTION');
            client.get(this.getPricingUnits.bind(this));
        } else {
            this.getPricingUnits([]);
        }
    };

    CreateOfferingForm.prototype.displayPricingEditor = function displayPricingEditor(units) {
        var footBtn, backBtn;

        // Set navigation button
        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-3').addClass('selected');
        setVisited($('#off-nav-3'));

        if (!$('#offering-creation-pricing').length) {
            this.units = units;
            this.pricingEditor = new PricingEditor($('.modal-body'), this.units, this.currencies);
            this.pricingEditor.createListeners();
        } else {
            $('#offering-creation-pricing').removeClass('hide');
        }

        $('.modal-footer').empty();
        backBtn = $('<input class="btn btn-basic" type="button" value="Back"></input>').appendTo('.modal-footer');
        backBtn.click(function(evnt) {
            $('#offering-creation-pricing').addClass('hide');
            this.showUSDLForm();
        }.bind(this));

        footBtn = $('<input class="btn btn-basic" type="button" value="Next"></input>').appendTo('.modal-footer');
        footBtn.click(function(){
            this.offeringInfo.offering_description.pricing = this.pricingEditor.getPricing();
            $('#offering-creation-pricing').addClass('hide');

            if (IDMAUTH) {
                this.getApplications();
            } else {
                if (!$('#offering-creation-resources').length) {
                    userForm = new BindResourcesForm({});
                    userForm.getUserResources(this.showResourcesForm.bind(this), this.offeringInfo.open, true);
                } else {
                    this.showResourcesForm([]);
                }
            }
        }.bind(this));
    };

    /**
     * Displays the form for providing the USDL info
     */
    CreateOfferingForm.prototype.showUSDLForm = function showUSDLForm() {
        var footBtn, backBtn;

        // Set navigation button
        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-2').addClass('selected');
        setVisited($('#off-nav-2'));

        // Create the form
        if (!$('#offering-creation-usdl').length) {
            $.template('usdlTemplate', $('#select_usdl_form_template'));
            $.tmpl('usdlTemplate').appendTo('.modal-body');
        } else {
            $('#offering-creation-usdl').removeClass('hide');
        }
        
        // Listener for application selection
        $('.modal-footer').empty();

        backBtn = $('<input class="btn btn-basic" type="button" value="Back"></input>').appendTo('.modal-footer');
        backBtn.click(function(evnt) {
            $('#offering-creation-usdl').addClass('hide');
            this.includeContents();
        }.bind(this));

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
            this.offeringInfo.offering_description = {
                'description': description,
                'abstract': abstract,
            }

            // Include the legal info if conpleted
            if (legal.title && legal.text) {
                this.offeringInfo.offering_description.legal = legal
            }

            // If the USDL is loaded go to the final step, application selection
            if (!error) {
                $('#offering-creation-usdl').addClass('hide');
                this.getAllowedCurrencies();
            } else {
                fillErrorMessage(msg, errElems, $('#error-message-usdl'));
            }
        }.bind(this));
    };

    /**
     * Obtains the idm applications of an user
     */
    CreateOfferingForm.prototype.getApplications = function getApplications () {
        if (!$('#offering-creation-apps').length) {
            $.ajax({
                type: "GET",
                url: EndpointManager.getEndpoint('APPLICATION_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                success: function (response) {
                    this.showApplicationsForm(response);
                }.bind(this),
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showAlertError('Error', msg, $('#error-message'));
                }
            });
        } else {
            this.showApplicationsForm([]);
        }
    };

    /**
     * Display the form for the selection of idM applications
     */
    CreateOfferingForm.prototype.showApplicationsForm = function showApplicationsForm(applications) {
        var userForm, footBtn, backBtn;
        var created = false;

        // Set navigation button
        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-4').addClass('selected');
        setVisited($('#off-nav-4'));

        // Create the form
        if (!$('#offering-creation-apps').length) {
            $.template('offDescTemplate', $('#select_application_form_template'));
            $.tmpl('offDescTemplate').appendTo('.modal-body');
            created = true;
        } else {
            $('#offering-creation-apps').children().off();
            $('#offering-creation-apps').removeClass('hide');
        }

        $('#app-help').popover({'trigger': 'manual'});
        $('#app-help').click(helpHandler);
        // Include applications
        if (applications.length > 0 && created) {
            $.template('appCheckTemplate', $('#application_select_template'));
            // Fill applications structure
            for (var i = 0; i < applications.length; i++) {
                var url = applications[i].url;
                var dispUrl = applications[i].url;
                this.apps[applications[i]['id']] = applications[i];

                // Check URL size
                if (applications[i].url.length > 50) {
                    dispUrl = url.substr(0, 50) + '...';
                }

                $.tmpl('appCheckTemplate', {
                    'name': applications[i].name,
                    'url': url,
                    'disp_url': dispUrl,
                    'id': applications[i].id
                }).appendTo('#applications');
            }
        } else if (created) {
            var msg = "You don't have any application available for access control. Go to the next window to bind some downloadable resources";
            MessageManager.showAlertInfo('No Applications', msg, $('#applications'));
        }

        // Set button listener
        $('.modal-footer').empty();
        backBtn = $('<input class="btn btn-basic" type="button" value="Back"></input>').appendTo('.modal-footer');
        backBtn.click(function(evnt) {
            $('#offering-creation-apps').addClass('hide');
            //$('#offering-creation-main').children().off();
            this.displayPricingEditor();
            //$('#offering-creation-main').removeClass('hide');
        }.bind(this));

        footBtn = $('<input></input>').addClass('btn btn-basic').attr('type', 'button').val('Next').appendTo('.modal-footer');
        footBtn.click(function(evnt) {
            var appsSelected = [];
            evnt.preventDefault();
            evnt.stopPropagation();

            if ($('#app-help').prop('displayed')) {
                $('#app-help').popover('hide');
                $('#app-help').prop('displayed', false);
                $('#app-help').removeClass('question-sing-sel');
                $(document).unbind('click');
            }

            // Check the selected applications
            $('input[type="checkbox"]').each(function(self) {
                return function() {
                    if ($(this).prop('checked') && self.apps.hasOwnProperty($(this).attr('id'))) {
                        var app = self.apps[$(this).attr('id')];
                        appsSelected.push({
                            'name': app.name,
                            'url': app.url,
                            'id': app.id,
                            'description': app.description
                        });
                    }
                }
            }(this));

            // Make the request
            this.offeringInfo.applications = appsSelected;

            $('#offering-creation-apps').addClass('hide');
            if (!$('#offering-creation-resources').length) {
                userForm = new BindResourcesForm({});
                userForm.getUserResources(this.showResourcesForm.bind(this), this.offeringInfo.open, true);
            } else {
                this.showResourcesForm([]);
            }
        }.bind(this));
    };

    /**
     * Displays the form for the selection of resources
     */
    CreateOfferingForm.prototype.showResourcesForm = function showResourcesForm(resources) {
        var backBtn, created = false;

        // Set navigation button
        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-5').addClass('selected');
        setVisited($('#off-nav-5'));

        $()
        $('.modal-footer').empty()

        if (!$('#offering-creation-resources').length) {
            $.template('selectResourcesTemplate', $('#resources_form_template'));
            $.tmpl('selectResourcesTemplate').appendTo('.modal-body');
            created = true;
        } else {
            $('#offering-creation-resources').children().off();
            $('#offering-creation-resources').removeClass('hide');
        }

        $('#resources-help').popover({'trigger': 'manual'});
        $('#resources-help').click(helpHandler);

        if (resources.length > 0 && created) {
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
            this.resources = resources
        } else if (created){
            var msg = "You don't have any resource registered. Press accept to create the offering without resources (You can bind resources later, before publishing the offering).";
            MessageManager.showAlertInfo('No Resources', msg, $('#sel-resources'));
        }

        backBtn = $('<input class="btn btn-basic" type="button" value="Back"></input>').appendTo('.modal-footer');
        backBtn.click(function(evnt) {
            $('#offering-creation-resources').addClass('hide');
            if (OILAUTH) {
                this.showApplicationsForm([]);
            } else {
                this.displayPricingEditor();
            }
        }.bind(this));

        // Append the Accept button
        $('<input></input>').attr('type', 'button').addClass('btn btn-blue').attr('value', 'Accept').click(function() {
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
                        'name': this.resources[i].name,
                        'version': this.resources[i].version
                    })
                }
            }
            this.offeringInfo.resources = resSelected;

            this.makeCreateOfferingRequest();
        }.bind(this)).appendTo('.modal-footer');
    };

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

    CreateOfferingForm.prototype.includeContents = function includeContents() {
        var i;

        $('#offering-creation-main').children().off();
        $('#offering-creation-main').removeClass('hide');

        $('.off-nav.selected').removeClass('selected');
        $('#off-nav-1').addClass('selected');
        setVisited($('#off-nav-1'));

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

        $('.modal-footer').empty();
        $('<input type="button" class="btn btn-basic" value="Next"></input>').appendTo('.modal-footer');

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
                $('#offering-creation-main').addClass('hide');
                this.showUSDLForm();
            } else {
                fillErrorMessage(msg, errElems)
            }
        }.bind(this));
    }
})();

