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

    /**
     * Constructor of the RegisterResourceForm
     * @param resInfo. Optional parameter that specified info of a resource
     * used to update resources instead of creating a new one
     * @returns {RegisterResourceForm}
     */
    RegisterResourceForm = function RegisterResourceForm(resInfo, msgId) {
        this.resource = {};
        this.msgId = '#message';

        if (resInfo) {
            this.resourceInfo = resInfo;
            if (msgId) {
                this.msgId = msgId;
            }
        }
        this.client = new ServerClient('RESOURCE_ENTRY', 'RESOURCE_COLLECTION');
    }

    // Register resource form is a subclass of modal form
    RegisterResourceForm.prototype = new ModalForm('Register new resource', '#register_res_form_template');
    RegisterResourceForm.prototype.constructor = RegisterResourceForm;


    /**
     * Private method used to handle the uploading of resources
     * @param evnt
     * @returns
     */
    var handleResourceSelection = function handleResourceSelection (evnt) {
        var f = evnt.target.files[0];
        var reader = new FileReader();
        this.resource = {};

        reader.onload = (function(file, self) {
            return function(e) {
                var binaryContent = e.target.result;
                // Check name format
                var nameReg = new RegExp(/^[\w\s-]+\.[\w]+$/);

                if (!nameReg.test(file.name)) {
                    this.resource.error = true;
                    this.resource.msg = 'Invalid file: Unsupported character in file name';
                } else {
                    this.resource.data = btoa(binaryContent);
                    this.resource.name = file.name;
                }
            }.bind(self);
        })(f, this);
        reader.readAsBinaryString(f);
    };

    /**
     * Private method used to handle help messages
     * @param evnt
     * @returns
     */
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

    var loadResource = function loadResource(self, request) {
        link = $.trim($(self.msgId + ' [name="res-link"]').val());
        if (!$.isEmptyObject(self.resource)) {
            // Check resource
            if (self.resource.error) {
                throw resource.msg;
            } else {
                request.content = self.resource;
            }
        } else if (link) {
            // Check link format
            var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
            if (!urlReg.test(link)) {
                throw 'Invalid URL format';
            } else {
                request.link = link;
            }
        }
    };
    /**
     * Private method that makes update request
     */
    var makeUpdateResRequest = function makeUpdateResRequest() {
        var request = {};
        var error = false;
        var resourceId = {
            'provider': ORGANIZATION,
            'name': this.resourceInfo.name,
            'version': this.resourceInfo.version
        }

        // Load content type and description
        if ($.trim($(this.msgId + ' [name="res-content-type"]').val()) &&
                $.trim($(this.msgId + ' [name="res-content-type"]').val()) != this.resourceInfo.content_type) {
            request.content_type = $.trim($(this.msgId + ' [name="res-content-type"]').val());
        }

        if ($.trim($(this.msgId + ' [name="res-description"]').val()) &&
                $.trim($(this.msgId + ' [name="res-description"]').val()) != this.resourceInfo.description) {
            request.description = $.trim($(this.msgId + ' [name="res-description"]').val());
        }

        if (this.resourceInfo.state != 'used') {
            // If the resource is not in use a complete update is allowed
            // Name
            if ($.trim($(this.msgId + ' [name="res-name"]').val()) &&
                    $.trim($(this.msgId + ' [name="res-name"]').val()) != this.resourceInfo.name) {

                var name = $.trim($(this.msgId + ' [name="res-name"]').val())
                // Check name format
                var nameReg = new RegExp(/^[\w\s-]+$/);
                if (name && !nameReg.test(name)) {
                    error = true;
                    msg = 'Invalid name format: Unsupported character';
                }
                request.name = name;
            }
            // Version
            if ($.trim($(this.msgId + ' [name="res-version"]').val()) &&
                    $.trim($(this.msgId + ' [name="res-version"]').val()) != this.resourceInfo.version) {
                version = $.trim($(this.msgId + ' [name="res-version"]').val());
                var versReg = new RegExp(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/);
                if (version && !versReg.test(version)) {
                    error = true;
                    msg = 'Invalid version format';
                }
                request.version = version;
            }
            // Resource
            try {
                loadResource(this, request);
            } catch(err) {
                error = true;
                msg = err;
            }
        }

        if (!error) {
            this.client.create(request, function (response) {
                $(this.msgId).modal('hide');
            }.bind(this), resourceId);
        } else {
            MessageManager.showAlertError('Error', msg, $(this.msgId + ' #error-container'));
        }
    };

    /**
     * Private method used to make requests to the server
     */
    var makeRegisterResRequest = function makeRegisterResRequest (evnt) {
         var name, version, link, contentType, request = {};
         var msg, error = false;

         evnt.preventDefault();
         evnt.stopPropagation();

         name = $.trim($(this.msgId + ' [name="res-name"]').val());
         version = $.trim($(this.msgId + ' [name="res-version"]').val());
         contentType = $.trim($(this.msgId + ' [name="res-content-type"]').val());
         description = $.trim($(this.msgId + ' [name="res-description"]').val());

         if (!name || !version) {
             error = true;
             msg = 'Missing required field(s):';
             if (!name) {
                 msg += ' Name';
             }
             if (!version) {
                 msg += ' Version';
             }
         }

         // Check name format
         var nameReg = new RegExp(/^[\w\s-]+$/);
         if (name && !nameReg.test(name)) {
             error = true;
             msg = 'Invalid name format: Unsupported character';
         }

         var versReg = new RegExp(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/);
         if (version && !versReg.test(version)) {
             error = true;
             msg = 'Invalid version format';
         }
         request.content_type = contentType
         request.name = name;
         request.version = version;
         request.description = description;
         request.open = $(this.msgId + ' #res-open').prop('checked');

         try {
             loadResource(this, request);
         } catch(err) {
             error = true;
             msg = err;
         }

         if (!error && !request.content && !request.link) {
             error = true;
             msg = "You have not provided a resource";
         }

         if (!error) {
             this.client.create(request, function (response) {
                 $(this.msgId).modal('hide');
                 MessageManager.showMessage('Created', 'The resource has been registered');
             }.bind(this));
         } else {
             MessageManager.showAlertError('Error', msg, $(this.msgId + ' #error-container'));
         }

    
    };

    /**
     * Method used to include the resource info in the different form
     * fields when the view is used for updating a resource
     */
    RegisterResourceForm.prototype.fillResourceInfo = function fillResourceInfo() {
        // Fill resource info
        $(this.msgId + ' [name="res-name"]').val(this.resourceInfo.name);
        $(this.msgId + ' [name="res-version"]').val(this.resourceInfo.version);
        $(this.msgId + ' [name="res-content-type"]').val(this.resourceInfo.content_type);
        $(this.msgId + ' [name="res-description"]').val(this.resourceInfo.description);

        $(this.msgId + ' [name="res-open"]').prop('checked', this.resourceInfo.open);

        // Disable fields depending on the state
        if (this.resourceInfo.state == 'used') {
            $(this.msgId + ' [name="res-name"]').prop('disabled', true);
            $(this.msgId + ' [name="res-version"]').prop('disabled', true);
            $(this.msgId + ' [name="res-open"]').prop('disabled', true);
            $(this.msgId + ' [name="res-type"]').prop('disabled', true);
            $(this.msgId + ' [name="files"]').prop('disabled', true);
        }
    };

    /**
     * Implementation of setListeners abstract method
     */
    RegisterResourceForm.prototype.setListeners = function setListeners() {
        var action = makeRegisterResRequest;

        //Set listeners
        $(this.msgId + ' #upload-help').click(helpHandler);
        $(this.msgId + ' #link-help').click(helpHandler);
        $(this.msgId + ' #open-help').click(helpHandler);

        $(this.msgId).on('hide', function() {
            $(document).unbind('click');
            $('.popover').remove();
        });

        $(this.msgId + ' #res-type').on('change', function(self) {
            return function() {
                self.resource= {};
                $(self.msgId + ' [name="res-link"]').val('');
                if ($(this).val() == 'upload') {
                    $(self.msgId +' #upload').removeClass('hide');
                    $(self.msgId + ' #upload-help').removeClass('hide');
                    $(self.msgId + ' [name="res-link"]').addClass('hide');
                    $(self.msgId + ' #link-help').addClass('hide');
                } else {
                    $(self.msgId + ' #upload').addClass('hide');
                    $(self.msgId + ' #upload-help').addClass('hide');
                    $(self.msgId + ' [name="res-link"]').removeClass('hide');
                    $(self.msgId + ' #link-help').removeClass('hide');
                }
            };
        }(this));

        // If the view is used to update a resource include resource info
        if (this.resourceInfo) {
            this.fillResourceInfo();
        }
        $(this.msgId + ' #upload').on('change', handleResourceSelection.bind(this));

        if (this.resourceInfo) {
            action = makeUpdateResRequest;
        }
        $(this.msgId + ' .modal-footer > .btn').click(action.bind(this));
    };

    /**
     * Implementation of includeContents abstract method
     */
    RegisterResourceForm.prototype.includeContents = function includeContents() {
        // Configure help messages
        $(this.msgId + ' #upload-help').popover({'trigger': 'manual'});
        $(this.msgId + ' #link-help').popover({'trigger': 'manual'});
        $(this.msgId + ' #open-help').popover({'trigger': 'manual'});
    };

})();
