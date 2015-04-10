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

(function() {

    var basicValidation = function basicValidation () {
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
                msg += 'Invalid name format <br/>';
                errFields.push($('#elem-name').parent().parent())
            }
                
            // Check host format
            var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
            if (!urlReg.test(host)) {
                validation.valid = false;
                msg += 'Invalid URL format <br/>';
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
            validation.msg = "Name and Host are required </br>";
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


    var deleteElementHandler = function deleteElementHandler (event) {
        var element = event.target;

        // Get the element name
        jqObject = jQuery(element);
        name = jqObject.parent().parent().parent().find('.elem-name').text();

        // Make a delete request 
        this.mainClient.remove(this.elementInfoRequest.bind(this), {
            'name': name
        });
    };


    RepositoryForm = function RepositoryForm () {
    };


    RepositoryForm.prototype = new AdminForm('REPOSITORY_ENTRY', 'REPOSITORY_COLLECTION', $('#form_template'), {'title': 'Repository'});
    RepositoryForm.prototype.constructor = RepositoryForm;

    RepositoryForm.prototype.fillListInfo = function fillListInfo(elements) {
        // Paint elements
        $.template('elemTemplate', $('#element_template'));
        $.tmpl('elemTemplate', elements).appendTo('#table-list');

        // Set delete listener
        $('.delete').click(deleteElementHandler.bind(this));
    };

    RepositoryForm.prototype.validateFields = function validateFields() {
        return basicValidation();
    }


    /**
     *
     */
    MarketplaceForm = function MarketplaceForm (argument) {
    };

    MarketplaceForm.prototype = new AdminForm('MARKET_ENTRY', 'MARKET_COLLECTION', $('#marketplace_form_template'), {'title': 'Marketplace'});
    MarketplaceForm.prototype.constructor = MarketplaceForm;

    MarketplaceForm.prototype.fillListInfo = function fillListInfo(elements) {
        // Paint elements
        $.template('elemTemplate', $('#element_template'));
        $.tmpl('elemTemplate', elements).appendTo('#table-list');

        // Set delete listener
        $('.delete').click(deleteElementHandler.bind(this));
    };

    MarketplaceForm.prototype.validateFields = function validateFields() {
        var validation = basicValidation();
        var api_version = $('#api-version').val();

        // Check credentials if needed
        if (api_version == '1' || !IDMAUTH) {
            var username = $.trim($('#cred-username').val());
            var passwd = $.trim($('#cred-passwd').val());
            var passwdConf = $.trim($('#cred-passwd-conf').val());

            if (!username || !passwd || !passwdConf) {
                validation.valid = false;
                validation.msg += 'All credentials fields are required </br>'

            } else if (passwd != passwdConf) {
                validation.valid = false;
                validation.msg += "Pasword and password confirmation don't match";
            } else {
                validation.data.credentials = {
                    'username': username,
                    'passwd': passwd
                }
            }

            if (!validation.valid) {
                if (!validation.errFields) {
                    validation.errFields = [];
                }

                validation.errFields.push($('#cred-username').parent().parent());
            }
        }

        // Include api version
        if (validation.valid) {
            validation.data.api_version = api_version;
        }

        return validation;
    }

    MarketplaceForm.prototype.setFormListeners = function setFormListeners() {
        // Check if the credentials field is needed
        if (IDMAUTH) {
            // Set listeners for hiding credentials for API version 2
            $('#api-version').change(function () {
                if ($(this).val() == '2') {
                    $('#market-cred').addClass('hide');
                } else {
                    $('#market-cred').removeClass('hide');
                }
            });
        }
    }
})();