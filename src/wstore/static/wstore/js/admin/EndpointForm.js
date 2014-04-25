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
     * Builder created to allow the creation of a parameterized
     * Admin form
     */
    EndpointFormBuilder = function EndpointFormBuilder(endpointType) {
        var entryUrl, collectionUrl, title;

        // Check the type of AdminForm to build
        if (endpointType == 'marketplace') {
            title = 'Marketplace';
            entryUrl = 'MARKET_ENTRY';
            collectionUrl = 'MARKET_COLLECTION';
        } else if (endpointType == 'repository') {
            title = 'Repository';
            entryUrl = 'REPOSITORY_ENTRY';
            collectionUrl = 'REPOSITORY_COLLECTION';
        } else {
            MessageManager.showMessage('Error', 'Incorrect endpoint type');
        }

        /**
         * Endpoint form constructor
         */
        EndpointForm = function EndpointForm() {
        };

        /**
         * Endpoint form is a subclass of AdminForm
         */
        EndpointForm.prototype = new AdminForm(entryUrl, collectionUrl, $('#form_template'), {'title': title});
        EndpointForm.prototype.constructor = EndpointForm;

        /**
         * Fill the list of endpoint elements (Marketplaces or repositories)
         */
        EndpointForm.prototype.fillListInfo = function fillListInfo(elements) {
            // Paint elements
            $.template('elemTemplate', $('#element_template'));
            $.tmpl('elemTemplate', elements).appendTo('#table-list');

            // Set delete listener
            $('.delete').click((function (event) {
                var element = event.target;

                // Get the element name
                jqObject = jQuery(element);
                name = jqObject.parent().parent().parent().find('.elem-name').text();

                // Make a delete request 
                this.mainClient.remove(this.elementInfoRequest.bind(this), {
                    'name': name
                });
            }).bind(this));
        };

        EndpointForm.prototype.validateFields = function validateFields() {
            var validation = {};

            name = $.trim($('#elem-name').val());
            host = $.trim($('#elem-host').val());

            if (name && host) {
                var urlReg, nameReg, msg = '', errFields = [];

                validation.valid = true;

                // Check name format
                nameReg = new RegExp(/^[\w\s-]+$/);
                if (!nameReg.test(name)) {
                    validation.valid = false;
                    msg += 'Invalid name format';
                    errFields.push($('#elem-name').parent().parent())
                }
                
                // Check host format
                var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
                if (!urlReg.test(host)) {
                    validation.valid = false;
                    msg += 'Invalid URL format';
                    errFields.push($('#elem-host').parent().parent());
                }

                // Fill validation missing info
                if (validation.valid) {
                    validation.data = {
                        'name': name,
                        'host': host
                    };
                } else {
                    validation.msg = msg;
                    validation.errFields = errFields;
                }
            } else {
                validation.valid = false;
                validation.msg = "Both fields are required";
                validation.errFields = []

                // Include fields with errors
                if (!name) {
                    validation.errFields.push($('#elem-name').parent().parent());
                }
                if(!host) {
                    validation.errFields.push($('#elem-host').parent().parent());
                }
            }
            return validation;
        };

        return new EndpointForm();
    };
})();