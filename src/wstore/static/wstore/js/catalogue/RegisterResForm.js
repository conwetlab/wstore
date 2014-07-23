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

    ResourceCreator = function ResourceCreator() {
    };

    ResourceCreator.prototype.makeRequest = function makeRequest(evnt) {
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
            this.loadResource(request);
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
            $('.alert-error').removeClass('span8');
        }

    };

    ResourceCreator.prototype.fillResourceInfo = function fillResourceInfo() {
    };

})();

(function() {

    ResourceUpdater = function ResourceUpdater() {
    };

    ResourceUpdater.prototype.makeRequest = function makeRequest(evnt) {
        var request = {};
        var error = false;
        var resourceId = {
            'provider': ORGANIZATION,
            'name': this.resourceInfo.name,
            'version': this.resourceInfo.version
        }

        evnt.preventDefault();
        evnt.stopPropagation();

        // Load description
        if ($.trim($(this.msgId + ' [name="res-description"]').val()) &&
                $.trim($(this.msgId + ' [name="res-description"]').val()) != this.resourceInfo.description) {
            request.description = $.trim($(this.msgId + ' [name="res-description"]').val());
        }

        if (this.resourceInfo.state != 'used') {
            // If the resource is not in use a complete update is allowed

            if ($.trim($(this.msgId + ' [name="res-content-type"]').val()) &&
                    $.trim($(this.msgId + ' [name="res-content-type"]').val()) != this.resourceInfo.content_type) {
                request.content_type = $.trim($(this.msgId + ' [name="res-content-type"]').val());
            }

            if ($(this.msgId + ' [name="res-open"]').prop('checked') != this.resourceInfo.open) {
                request.open = $(this.msgId + ' [name="res-open"]').prop('checked');
            }
        }

        if (!error) {
            this.client.update(request, function (response) {
                $(this.msgId).modal('hide');
            }.bind(this), resourceId, function(xhr) {

                $(this.msgId).off('hidden');

                $(this.msgId).modal('hide');

                // Remove modal
                $(this.msgId).remove();
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;

                // Show new modal
                MessageManager.showMessage('Error', msg, $('#new-container'));
                $(this.msgId).off('hidden');
                $(this.msgId).on('hidden', this.caller.showModal.bind(this.caller));

            }.bind(this));
        } else {
            MessageManager.showAlertError('Error', msg, $(this.msgId + ' #error-container'));
            $('.alert-error').removeClass('span8');
        }
    };

    ResourceUpdater.prototype.fillResourceInfo = function fillResourceInfo() {
        // Fill resource info
        $(this.msgId + ' [name="res-name"]').val(this.resourceInfo.name);
        $(this.msgId + ' [name="res-version"]').val(this.resourceInfo.version);
        $(this.msgId + ' [name="res-content-type"]').val(this.resourceInfo.content_type);
        $(this.msgId + ' [name="res-description"]').val(this.resourceInfo.description);

        $(this.msgId + ' [name="res-open"]').prop('checked', this.resourceInfo.open);

        // Remove unnecessary fields
        $(this.msgId + ' [name="res-name"]').prop('disabled', true);
        $(this.msgId + ' [name="res-version"]').prop('disabled', true);

        $(this.msgId + ' [name="res-type"]').remove();
        $(this.msgId + ' [name="files"]').remove();
        $(this.msgId + ' [name="res-link"]').remove();
        $(this.msgId + ' #link-help').remove();
        $(this.msgId + ' #upload-help').remove();
        $(this.msgId + ' label:contains(Select how to provide the resource)').remove();

        // Disable fields depending on the state
        if (this.resourceInfo.state == 'used') {
            $(this.msgId + ' [name="res-content-type"]').prop('disabled', true);
            $(this.msgId + ' [name="res-open"]').prop('disabled', true);
        }
    };
})();

(function() {

    ResourceUpgrader = function ResourceUpgrader() {
    };

    ResourceUpgrader.prototype.makeRequest = function makeRequest(evnt) {
        var msg, error = false;
        var request = {};
        var resourceId = {
            'provider': ORGANIZATION,
            'name': this.resourceInfo.name,
            'version': this.resourceInfo.version
        }
        var version = $(this.msgId + ' [name="res-version"]').val();

        evnt.preventDefault();
        evnt.stopPropagation();

        // validate version value
        if (!version) {
            error = true;
            msg = 'Missing required field: Version';
        }

        if (!error) {
            var versReg = new RegExp(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/);
            if (version && !versReg.test(version)) {
                error = true;
                msg = 'Invalid version format';
            }
        }

        request.version = version;

        // Load resource
        if (!error) {
            try {
                this.loadResource(request);
            } catch(err) {
                error = true;
                msg = err;
            }
        }

        if (!error && !request.content && !request.link) {
            error = true;
            msg = "You have not provided a resource";
        }

        // Make server request
        if (!error) {
            this.client.create(request, function (response) {
                $(this.msgId).modal('hide');
            }.bind(this), resourceId, function(xhr) {
                $(this.msgId).off('hidden');

                $(this.msgId).modal('hide');

                // Remove modal
                $(this.msgId).remove();
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;

                // Show new modal
                MessageManager.showMessage('Error', msg, $('#new-container'));
                $(this.msgId).off('hidden');
                $(this.msgId).on('hidden', this.caller.showModal.bind(this.caller));

            }.bind(this));
        } else {
            MessageManager.showAlertError('Error', msg, $(this.msgId + ' #error-container'));
            $('.alert-error').removeClass('span8');
        }
    };

    ResourceUpgrader.prototype.fillResourceInfo = function fillResourceInfo() {
        $(this.msgId + ' [name="res-name"]').val(this.resourceInfo.name);

        // Remove unnecessary fields
        $(this.msgId + ' [name="res-name"]').prop('disabled', true);

        $(this.msgId + ' [name="res-version"]').val(this.resourceInfo.version);
        $(this.msgId + ' [name="res-content-type"]').remove();
        $(this.msgId + ' label:contains(Content type)').remove();
        $(this.msgId + ' [name="res-description"]').remove();
        $(this.msgId + ' label:contains(Description)').remove();

        $(this.msgId + ' [name="res-open"]').remove();
        $(this.msgId + ' #open-help').remove();
        $(this.msgId + ' span:contains( Open Resource )').remove();
    };

})();

buildRegisterResourceForm = function buildRegisterResourceForm(builder, resourceInfo, messageId, caller) {

    // Select builder
    var builders = {
        'create': ResourceCreator,
        'edit': ResourceUpdater,
        'upgrade': ResourceUpgrader
    };

    var titles = {
        'create': 'Register new resource',
        'edit': 'Edit resource',
        'upgrade': 'Upgrade resource'
    };

    /**
     * Constructor of the RegisterResourceForm
     * @param resInfo. Optional parameter that specified info of a resource
     * used to update resources instead of creating a new one
     * @returns {RegisterResourceForm}
     */
    RegisterResourceForm = function RegisterResourceForm(builderObj, resInfo, msgId, caller) {
        this.builderObj = builderObj;
        this.resource = {};
        this.msgId = '#message';

        if (resInfo) {
            this.resourceInfo = resInfo;
            if (msgId) {
                this.msgId = msgId;
            }
        }

        if (caller) {
            this.caller = caller;
        }
        this.client = new ServerClient('RESOURCE_ENTRY', 'RESOURCE_COLLECTION');
    }

    // Register resource form is a subclass of modal form
    RegisterResourceForm.prototype = new ModalForm(titles[builder], '#register_res_form_template');
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

    RegisterResourceForm.prototype.loadResource = function loadResource(request) {
        link = $.trim($(self.msgId + ' [name="res-link"]').val());
        if (!$.isEmptyObject(this.resource)) {
            // Check resource
            if (this.resource.error) {
                throw resource.msg;
            } else {
                request.content = this.resource;
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
     * Implementation of setListeners abstract method
     */
    RegisterResourceForm.prototype.setListeners = function setListeners() {
        var filler;

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
        filler = this.builderObj.fillResourceInfo.bind(this);
        filler();

        $(this.msgId + ' #upload').on('change', handleResourceSelection.bind(this));

        $(this.msgId + ' .modal-footer > .btn').click(this.builderObj.makeRequest.bind(this));
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

    return new RegisterResourceForm(new builders[builder](), resourceInfo, messageId, caller);
};
