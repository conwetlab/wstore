/*
 * Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid
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

    var displayPluginForm = function displayPluginForm(self) {
        // Build the form HTML
        var formGenerator = new FormGenerator();
        var htmlForm = formGenerator.generateForm(self.plugin.form);

        $(self.msgId + ' .modal-body').empty();

        $.template('pluginFormTemplate', htmlForm);
        $.tmpl('pluginFormTemplate').appendTo(self.msgId + ' .modal-body');

        // Bind new click listener
        // Fill new listener
        $(self.msgId + ' .modal-footer > .btn').off();
        $(self.msgId + ' .modal-footer > .btn').click(function(evnt) {
            var msg = "";
            var errFields = [];
            var meta = {}

            evnt.preventDefault();
            evnt.stopPropagation();

            // Read fields and populate meta field
            for (key in this.plugin.form) {

                if (this.plugin.form.hasOwnProperty(key)) {
                    var inputInfo = this.plugin.form[key];
                    var value;
                    var input = $(this.msgId + ' [name="' + key +'"]');

                    // Get value of the field
                    if (inputInfo.type == 'textarea') {
                        value = $.trim(input.text());

                    } else if (inputInfo.type == 'checkbox') {
                        value = input.prop('checked');

                    } else {
                        value = $.trim(input.val());
                    }

                    // Check if the field is mandatory
                    if ((inputInfo.type == 'text' || inputInfo.type == 'textarea')
                        && inputInfo.mandatory && !value) {

                            msg += msg + 'Missing required field: ' + key + '<br />';
                            errFields.push(input);
                    }

                    meta[key] = value;
                }
            }
            if (!errFields.length) {
                this.request.meta = meta;
                createResource(this);
            } else {
                showErrorMessage(this, errFields, msg);
            }

        }.bind(self));
    };

    var showErrorMessage = function showErrorMessage (self, errFields, msg) {
        var span;
        MessageManager.showAlertError('Error', '', $(self.msgId + ' #error-container'));
        span = $('<span></span>').appendTo('.alert-error');
        span[0].innerHTML = msg;
        $('.alert-error').removeClass('span8').on('close', function() {
            $('.error').removeClass('error');
        });

        // Mark error fields
        for (var i = 0; i < errFields.length; i++) {
            errFields[i].parent().parent().addClass('error');
        }
    };

    var displayProvideResForm = function displayProvideResForm(self) {
        $(self.msgId + ' .modal-body').empty();

        // Render template
        $.template('provideResTemplate', $('#provide_res_form_template'));
        $.tmpl('provideResTemplate').appendTo(self.msgId + ' .modal-body');

        // Include plugin specific interface if needed
        if (self.plugin) {
            // - Check if the plugin define concrete media types
            if (self.plugin.media_types.length > 0) {
                var select = $('<select name="res-content-type"></select>');

                $(self.msgId + ' [name="res-content-type"]').remove();

                // Include allowed media types
                for (var i = 0;  i < self.plugin.media_types.length; i++) {
                    var media_type = self.plugin.media_types[i];

                    $('<option val="' + media_type + '">' + media_type + '</option>')
                        .appendTo(select);
                }
                select.appendTo('#res-content-type-cont');
            }

            // Check allowed formats in the plugin
            if (self.plugin.formats.length == 1) {
                // Hide select
                $('#res-type-container').addClass('hide');

                if (self.plugin.formats[0] == 'FILE') {
                    // Hide URL
                    self.uploadHandler();
                } else {
                    // Hide file
                    self.linkHandler();
                }
            }
        }

        $(self.msgId + ' #upload-help').popover({'trigger': 'manual'});
        $(self.msgId + ' #link-help').popover({'trigger': 'manual'});
        $(self.msgId + ' #upload-help').click(self.helpHandler);
        $(self.msgId + ' #link-help').click(self.helpHandler);

        self.selectFormatHandler();
        $(self.msgId + ' #upload').on('change', self.handleResourceSelection.bind(self));

        // Fill new listener
        $(self.msgId + ' .modal-footer > .btn').off();
        $(self.msgId + ' .modal-footer > .btn').click(function(evnt) {
            var errFields = [];
            var msg = "";
            var content_type;

            evnt.preventDefault();
            evnt.stopPropagation();

            // Include resource
            try {
                this.loadResource(this.request);
            } catch(err) {
                msg += err + '<br />';
                errFields.push($(this.msgId + ' [name="files"]'));
            }

            if (!this.request.content && !this.request.link) {
                msg += "You have not provided a resource <br/>";
                errFields.push($(this.msgId + ' [name="files"]'));
            }

            // Include  content type
            content_type = $(this.msgId + ' [name="res-content-type"]').val();
            if (!content_type) {
                msg += 'Missing required field: Content type';
                errFields.push($(this.msgId + ' [name="res-content-type"]'));
            }

            this.request.content_type = content_type;

            // Display the plugin form if it is required
            if (!errFields.length) {
                if (this.plugin && this.plugin.form) {
                    displayPluginForm(this)
                } else {
                    createResource(this);
                }
            } else {
                showErrorMessage(this, errFields, msg);
            }
        }.bind(self));
    };

    ResourceCreator.prototype.makeRequest = function makeRequest(evnt) {
        var name, version, resourceType, description, open;
        var msg = "";
        var errFields = [];
        this.request = {}

        evnt.preventDefault();
        evnt.stopPropagation();

        // Load previous info
        name = $.trim($(this.msgId + ' [name="res-name"]').val());
        version = $.trim($(this.msgId + ' [name="res-version"]').val());
        resourceType = $(this.msgId + ' #resource-type').val();
        description = $.trim($(this.msgId + ' [name="res-description"]').val());

        if (!name || !version) {
            error = true;
            msg += 'Missing required field(s):';
            if (!name) {
                msg += ' Name';
                errFields.push($(this.msgId + ' [name="res-name"]'));
            }
            if (!version) {
                msg += ' Version';
                errFields.push($(this.msgId + ' [name="res-version"]'));
            }
            msg += '<br/>'
        }

        // Check name format
        var nameReg = new RegExp(/^[\w\s-]+$/);
        if (name && !nameReg.test(name)) {
            error = true;
            msg += 'Invalid name format: Unsupported character <br/>';
            errFields.push($(this.msgId + ' [name="res-name"]'));
        }

        var versReg = new RegExp(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/);
        if (version && !versReg.test(version)) {
            error = true;
            msg += 'Invalid version format <br />';
            errFields.push($(this.msgId + ' [name="res-version"]'));
        }
        this.request.resource_type = resourceType
        this.request.name = name;
        this.request.version = version;
        this.request.description = description;
        this.request.open = $(this.msgId + ' #res-open').prop('checked');

        this.setPlugin(resourceType);

        // Change modal form
        if (!errFields.length) {
            displayProvideResForm(this);
        } else {
            showErrorMessage(this, errFields, msg);
        }
    };

    var createResource = function createResource(self) {
        self.client.create(self.request, function (response) {
            $(this.msgId).modal('hide');
            MessageManager.showMessage('Created', 'The resource has been registered');
        }.bind(self));
    };

    ResourceCreator.prototype.fillResourceInfo = function fillResourceInfo() {
    };

})();

(function() {

    ResourceUpdater = function ResourceUpdater() {
    };

    ResourceUpdater.prototype.makeRequest = function makeRequest(evnt) {
        var request = {};
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
    };

    var fillContentTypeInput = function fillContentTypeInput (self) {
        var input;
        var generateForm = new FormGenerator();
        var inputValues = {
            'label': 'Content type',
            'default': self.resourceInfo.content_type
        }

        if (self.plugin.media_types.length > 0) {
            var options = [];

            for (var i = 0; i < self.plugin.media_types.length; i++) {
                options.push({
                    'value': self.plugin.media_types[i],
                    'text': self.plugin.media_types[i]
                })
            };
            inputValues.options = options;
            input = generateForm.generateSelectInput("res-content-type", inputValues);
        } else {
            inputValues.placeholder = 'Content type';
            input = generateForm.generateTextInput("res-content-type", inputValues);
        }

        input.appendTo(self.msgId + ' section.span5');
    };

    ResourceUpdater.prototype.fillResourceInfo = function fillResourceInfo() {

        this.setPlugin(this.resourceInfo.resource_type);

        // Fill resource info
        $(this.msgId + ' [name="res-name"]').val(this.resourceInfo.name);
        $(this.msgId + ' [name="res-version"]').val(this.resourceInfo.version);
        $(this.msgId + ' [name="res-description"]').val(this.resourceInfo.description);

        $(this.msgId + ' [name="res-open"]').prop('checked', this.resourceInfo.open);

        // Disable unnecessary fields
        $(this.msgId + ' [name="res-name"]').prop('disabled', true);
        $(this.msgId + ' [name="res-version"]').prop('disabled', true);
        $(this.msgId + ' #resource-type').prop('disabled', true);

        fillContentTypeInput(this);

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
        var msg = '';
        var error = false;
        var errFields = [];
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
            msg += 'Missing required field: Version <br />';
            errFields.push($(this.msgId + ' [name="res-version"]'));
        }

        if (!error) {
            var versReg = new RegExp(/^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$/);
            if (version && !versReg.test(version)) {
                error = true;
                msg += 'Invalid version format <br />';
                errFields.push($(this.msgId + ' [name="res-version"]'));
            }
        }

        request.version = version;

        // Load resource
        if (!error) {
            try {
                this.loadResource(request);
            } catch(err) {
                error = true;
                msg += err + '<br />';
                errFields.push($(this.msgId + ' [name="files"]'));
            }
        }

        if (!error && !request.content && !request.link) {
            error = true;
            msg += "You have not provided a resource <br />";
            errFields.push($(this.msgId + ' [name="files"]'));
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
            var span;
            MessageManager.showAlertError('Error', '', $(this.msgId + ' #error-container'));
            span = $('<span></span>').appendTo('.alert-error');
            span[0].innerHTML = msg;
            $('.alert-error').removeClass('span8').on('close', function() {
                $('.error').removeClass('error');
            });

            // Mark error fields
            for (var i = 0; i < errFields.length; i++) {
                errFields[i].parent().parent().addClass('error');
            }
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
     * Method used to handle the uploading of resources
     * @param evnt
     * @returns
     */
    RegisterResourceForm.prototype.handleResourceSelection = function handleResourceSelection (evnt) {
        var f = evnt.target.files[0];
        var reader = new FileReader();
        this.resource = {};

        reader.onload = (function(file, self) {
            return function(e) {
                var binaryContent = e.target.result;
                // Check name format
                var nameReg = new RegExp(/^[\w\s-.]+\.[\w]+$/);

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
     * Method used to handle help messages
     * @param evnt
     * @returns
     */
    RegisterResourceForm.prototype.helpHandler = function helpHandler(evnt) {
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
        link = $.trim($(this.msgId + ' [name="res-link"]').val());
        if (!$.isEmptyObject(this.resource)) {
            // Check resource
            if (this.resource.error) {
                throw this.resource.msg;
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

    RegisterResourceForm.prototype.linkHandler = function linkHandler () {
        $(this.msgId + ' #upload').addClass('hide');
        $(this.msgId + ' #upload-help').addClass('hide');
        $(this.msgId + ' [name="res-link"]').removeClass('hide');
        $(this.msgId + ' #link-help').removeClass('hide');
    };

    RegisterResourceForm.prototype.uploadHandler = function uploadHandler () {
        $(this.msgId +' #upload').removeClass('hide');
        $(this.msgId + ' #upload-help').removeClass('hide');
        $(this.msgId + ' [name="res-link"]').addClass('hide');
        $(this.msgId + ' #link-help').addClass('hide');
    };

    /**
     * Creates the handler for managing the selection of how to provide the
     * resource, upload or url
     */
    RegisterResourceForm.prototype.selectFormatHandler = function selectFormatHandler () {
        $(this.msgId + ' #res-type').on('change', function(self) {
            return function() {
                self.resource= {};
                $(self.msgId + ' [name="res-link"]').val('');
                if ($(this).val() == 'upload') {
                    self.uploadHandler();
                } else {
                    self.linkHandler();
                }
            };
        }(this));
    };

    /**
     * Implementation of setListeners abstract method
     */
    RegisterResourceForm.prototype.setListeners = function setListeners() {
        var filler;

        //Set listeners
        $(this.msgId + ' #open-help').click(this.helpHandler);

        $(this.msgId).on('hide', function() {
            $(document).unbind('click');
            $('.popover').remove();
        });

        // If the view is used to update a resource include resource info
        filler = this.builderObj.fillResourceInfo.bind(this);
        filler();

        $(this.msgId + ' #upload').on('change', this.handleResourceSelection.bind(this));

        $(this.msgId + ' .modal-footer > .btn').click(this.builderObj.makeRequest.bind(this));
    };

    /**
     * Include plugin info
     */
    RegisterResourceForm.prototype.setPluginInfo = function setPluginInfo(pluginInfo) {
        this.pluginInfo = pluginInfo;
    };

    RegisterResourceForm.prototype.setPlugin = function setPlugin (resourceType) {
        // Save plugin object selected
        var found = false;
        for (var i = 0; i < this.pluginInfo.length && !found; i++) {
            if (this.pluginInfo[i].name == resourceType) {
                found = true;
                this.plugin = this.pluginInfo[i];
            }
        }
    };

    /**
     * Implementation of includeContents abstract method
     */
    RegisterResourceForm.prototype.includeContents = function includeContents() {
        // Configure help messages
        $(this.msgId + ' #open-help').popover({'trigger': 'manual'});

        // Add plugin types
        for (var i = 0; i < this.pluginInfo.length; i++) {
            $(this.msgId + ' #resource-type').append('<option value="'+ this.pluginInfo[i].name + '">' + this.pluginInfo[i].name + '</option>');
        }
    };

    return new RegisterResourceForm(new builders[builder](), resourceInfo, messageId, caller);
};

/**
 * Open a resource modal after loading resource plugin info
 */
openResourceView = function openResourceView(builder, resourceInfo, messageId, caller, container, callback) {
    // Retrieve resource types
    plugin_client = new ServerClient('', 'PLUGINS_COLLECTION');

    plugin_client.get(function(pluginInfo) {
        var resModal = buildRegisterResourceForm(builder, resourceInfo, messageId, caller);
        resModal.setPluginInfo(pluginInfo);
        resModal.display(container);

        // Call the callback if needed
        if(callback) {
            callback();
        }
    });
}