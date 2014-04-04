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

    /*
     * Organization Form constructor
     */
    OrganizationForm = function OrganizationForm() {
    };

    /*
     * Organization form is a subclass of AdminForm
     */
    OrganizationForm.prototype = new AdminForm('ORGANIZATION_ENTRY', 'ORGANIZATION_COLLECTION', $('#organization_form_template'));
    OrganizationForm.prototype.constructor = OrganizationForm;

    /*
     * Implementation of validateFields abstract method, validate
     * Organization form and get form info
     */
    OrganizationForm.prototype.validateFields = function validateFields() {
        var validation = {};
        var filled = 0, fields = 0;

        validation.valid = true;

        var name = $.trim($('#org-name').val());
        var notification_url = $.trim($('#notify-url').val());

        // Check the name
        if (!name) {
            validation.valid = false;
            validation.msg = 'Missing required field';
            validation.errFields = [$('#org-name').parent().parent()];
        }

        // Check the notification url
        if (!notification_url) {
            if (validation.valid) {
                validation.valid = false;
                validation.msg = 'Missing required field';
                validation.errFields = [$('#notify-url').parent().parent()];
            } else {
                validation.errFields.push($('#notify-url').parent().parent());
            }
            return validation;
        } else {
            var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
            if (!urlReg.test(notification_url)) {
                if (!validation.valid) {
                    // Change validation message to indicate that more that an error exists
                    validation.msg += ' and invalid URL format';
                    validation.errFields.push($('#notify-url').parent().parent());
                } else {
                    validation.valid = false;
                    validation.msg = 'Invalid URL format';
                    validation.errFields = [$('#notify-url').parent().parent()];
                }
                return validation;
            }
        }

        // Get the credit card's input fields
        $('.credit-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            fields += 1;
        });

        // Get the credit card's select fields
        $('.credit-select').each(function() {
            if ($.trim($(this).val()) != 0) {
                filled += 1;
            }
            fields += 1;
        });

        // The credit card info is not required; however, if it is wanted to
        // provide it all fields are required.
        if (filled != 0 && filled != fields) {
            validation.valid = false;
            validation.msg = 'To provide a credit card all fields are required';
            validation.errFields = [];
            $('.credit-input').each(function() {
                if ($.trim($(this).val()).length == 0) {
                filled += 1;
                validation.errFields.push($(this).parent().parent());
                }
            });
            $('.credit-select').each(function() {
                if ($.trim($(this).val()) == 0) {
                filled += 1;
                validation.errFields.push($(this).parent().parent());
                }
            });
            return validation;
        }

        filled = 0;
        fields = 0;

        // Get the tax address
        $('.addr-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            fields += 1;
        });

        // The tax address is not required; however, if it is wanted to
        // provide it all fields are required.
        if (filled != 0 && filled != fields) {
            validation.valid = false;
            validation.msg = 'To provide a tax address all fields are required';
            validation.errFields = [];
            $('.addr-input').each(function() {
                if ($.trim($(this).val()).length == 0) {
                filled += 1;
                validation.errFields.push($(this).parent().parent());
                }
            });
        }
        
        return validation;
    };

    /**
     * Display the Organization form and fill the Organization entry info for updating
     */
    OrganizationForm.prototype.fillOrganizationInfo = function fillOrganizationInfo(organization) {

        // Paint the form
        this.paintForm();

        // Fill Organization entry info        
        $('#org-name').val(organization.name).prop('readonly', true);
        $('#notify-url').val(organization.notification_url);

        if (organization.payment_info) {
            credit_card = organization.payment_info
            $('#type').val(credit_card.type);
            $('#number').val(credit_card.number);
            $('#expire-month').val(credit_card.expire_month);
            $('#expire-year').val(credit_card.expire_year);
            $('#cvv2').val(credit_card.cvv2);
        }

        if (organization.tax_address) {
            tax_address = organization.tax_address;
            $('#street').val(tax_address.street);
            $('#postal').val(tax_address.postal);
            $('#city').val(tax_address.city);
            $('#country').val(tax_address.country);
        }
        // Change register button by an update button
        $('#elem-submit').val('Update').unbind('click').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.updateElementRequest({'org': organization.name});
        }).bind(this));
    };

    /*
     * Implementation of fillListInfo abstract method, includes
     * Organizations in the list view
     */
    OrganizationForm.prototype.fillListInfo = function fillListInfo(organizations) {
        $.template('elementTemplate', $('#element_template'));

        for (var i = 0; i < organizations.length; i++) {
            var editIcon;

            var template = $.tmpl('elementTemplate', {
                'name': organizations[i].name,
            });

            // Include edit icon
            editIcon = $('<i></i>').addClass('icon-edit').click((function(self, organizationEntry) {
                return function() {
                    self.fillOrganizationInfo(organizationEntry);
                };
            })(this, organizations[i]));
            
            template.find('#elem-info').append(editIcon);

            // Include delete listener
            template.find('.delete').click((function(self, organizationEntry) {
                return function() {
                    var urlContext = {
                        'name': organizationEntry.name
                    }
                    self.mainClient.remove(self.elementInfoRequest.bind(self), urlContext);
                };
            })(this, organizations[i]));

            // Append entry
            template.appendTo('#table-list');
        }
    };

    /*
     * Implementation of setFormListeners abstract method, creates
     * extra listeners included in the form
     */
    OrganizationForm.prototype.setFromListeners = function setFormListeners() {};

})();