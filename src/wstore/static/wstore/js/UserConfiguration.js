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

    /**
     * Constructs the configuration form of an user profile
     * @param userProfile Object with user info
     */
    UserConfForm = function UserConfForm(userProfile, isOrg) {
        this.isOrg = isOrg;
        this.userProfile = userProfile;
        this.userFormDisplayed = false;
        this.addrFormDisplayed = false;
        this.paymentFormDisplayed = false;

        if($('#expenditure-tab').lenght) {
            this.expenditureFormDisplayed = false;
        }
    };

    /**
     * UserConfForm is a subclass of ModalForm
     */
    UserConfForm.prototype = new ModalForm('Settings',  '#user_conf_template');

    UserConfForm.prototype.constructor = UserConfForm;

    /**
     * Update the user profile with edit forms info
     */
    UserConfForm.prototype.makeUpdateProfileRequest = function makeUpdateProfileRequest() {
        var filled, msg, error = false;
        var request = {};
        var notification = $.trim($('#not-input').val());
        var errorFields = [];

        // Check notification URL format
        var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
        if (notification && !urlReg.test(notification)) {
            error = true;
            msg = 'The notification URL provided has an invalid format';
            errorFields.push($('#not-input'));
        } else {
            request.notification_url = notification;
        }

        if (!this.isOrg) {
            // Load user info
            request.username = this.userProfile.getUsername();
            request.complete_name = $.trim($('#complete-name').val());
        } else {
            request.name = this.userProfile.getUsername();
        }
        // Load tax address
        filled = 0;

        $('.tax-input').each(function(evnt) {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            } else {
                errorFields.push($(this));
            }
        });

        // If any field is filled all fields must be filled
        if (filled != 0) {
            if (filled != 4) {
                error = true;
                msg = 'If a field of tax address is filled all fields must be filled';
            } else {
                request.tax_address = {
                    'street': $.trim($('#street').val()),
                    'postal': $.trim($('#postal').val()),
                    'city': $.trim($('#city').val()),
                    'province': $.trim($('#province').val()),
                    'country': $.trim($('#country').val())
                };
            }
        }

        if ($('#expenditure-tab').length) {
            var limitTypes = ['perTransaction', 'daily', 'weekly', 'monthly'];
            // Load expenditure limits
            request.limits = {}
            for (var i = 0; i < limitTypes.length; i++) {
                // Check if the field is filled
                if ($.trim($('#' + limitTypes[i]).val())) {
                    var value = $.trim($('#' + limitTypes[i]).val());
                    // Check that the value is a number
                    if ($.isNumeric(value) && Number(value) > 0) {
                        request.limits[limitTypes[i]] = value;
                    } else {
                        error = true;
                        msg = 'Expenditure limits must be positive numbers';
                        errorFields.push($('#' + limitTypes[i]));
                    }
                }
            }
        }

        // If not error occurred
        if (!error) {
            this.userProfile.updateProfile(request, this.display.bind(this), this.manageError.bind(this));
        } else {
            MessageManager.showAlertError('Error', msg, $('#error-message'));
            for (var i = 0; i < errorFields.length; i++) {
                errorFields[i].addClass('error-input');
            }
            //$('#error-message .close').remove();
        }
    };

    UserConfForm.prototype.manageError = function manageError() {
        this.modalCreated = false;
    };

    var getRolesString = function getRolesString(self) {
        var roles = '';
        var currentRoles = self.userProfile.getCurrentRoles();

        for (var i = 0; i < currentRoles.length; i++) {
            roles += (' ' + currentRoles[i] + ',');
        }
        return roles;
    }
    /**
     * Displays the form for updating the user info
     */
    UserConfForm.prototype.paintEditUserInfoForm = function paintEditUserInfoForm() {
        if (!this.userFormDisplayed) {
            var context;

            this.userFormDisplayed = true;

            $('#main-info').empty();

            // Load the user info
            context = {
                'name': this.userProfile.getUsername(),
                'url': this.userProfile.getNotificationUrl()
            }

            if (!this.isOrg) {
                context['complete_name'] = this.userProfile.getCompleteName();
                context['roles'] = getRolesString(this);
                $.template('infoFormTemplate', $('#user_info_form_template'));
            } else {
                $.template('infoFormTemplate', $('#org_info_form_template'));
            }
            $.tmpl('infoFormTemplate', context).appendTo('#main-info');
        }
    };

    /**
     * Displays the form for updating the tax address
     */
    UserConfForm.prototype.paintEditTaxAddrForm = function paintEditTaxAddr() {
        if (!this.addrFormDisplayed) {
            var context;
            var taxAddr = this.userProfile.getTaxAddress();

            this.addrFormDisplayed = true;

            $('#taxaddr-tab').empty();

            if (taxAddr) {
                context = {
                    'street': taxAddr.street,
                    'postal': taxAddr.postal,
                    'city': taxAddr.city,
                    'province': taxAddr.province
                };
            } else {
                context = {
                    'street': '',
                    'postal': '',
                    'city': '',
                    'province': '',
                    'country': ''
                };
            }

            $.template('addressConfFormTemplate', $('#address_conf_form_template'));
            $.tmpl('addressConfFormTemplate', context).appendTo('#taxaddr-tab');
            // Fill country
            if (taxAddr) {
                $('#country').val(taxAddr.country);
            }
        }
    };

    /**
     * Displays the form for updating the payment info
     */
    UserConfForm.prototype.paintEditPaymentInfoForm = function paintEditPaymentInfo() {
        if (!this.paymentFormDisplayed) {
            var context, month, type;
            var paymentInfo = this.userProfile.getPaymentInfo()

            this.paymentFormDisplayed = true;

            $('#paymentinfo-tab').empty();

            if (paymentInfo) {
                context = {
                    'number': paymentInfo.number,
                    'year': paymentInfo.expire_year,
                    'cvv2': paymentInfo.cvv2
                };
                month = paymentInfo.expire_month;
                type = paymentInfo.type;
            } else {
                context = {
                    'number': '',
                    'year': '',
                    'cvv2': ''
                };
                month = '';
                type = '';
            }

            $.template('paymentInfoFormTemplate', $('#payment_info_form_template'));
            $.tmpl('paymentInfoFormTemplate', context).appendTo('#paymentinfo-tab');

            $('#type').val(type);
            $('#expire-month').val(month);
        }
    };

    UserConfForm.prototype.paintExpenditureForm = function paintExpenditureForm() {
        if (!this.expenditureFormDisplayed) {
            var expenditureInfo = this.userProfile.getExpenditureInfo();

            $('#expenditure-tab').empty();
            $.template('expenditureInfoFormTemplate', $('#expenditure_conf_form_template'));
            if (expenditureInfo) {
                $.tmpl('expenditureInfoFormTemplate', expenditureInfo).appendTo('#expenditure-tab');
            } else {
                $.tmpl('expenditureInfoFormTemplate', expenditureInfo).appendTo('#expenditure-tab');
            }
        }
    };

    /**
     * Switch the user configuration form from display to edit mode
     */
    UserConfForm.prototype.displayEditProfileForm = function displayEditProfileForm() {

        this.userFormDisplayed = false;
        this.addrFormDisplayed = false;
        this.paymentFormDisplayed = false;

        this.paintEditUserInfoForm();
        this.paintEditTaxAddrForm();
        this.paintEditPaymentInfoForm();

        if($('#expenditure-tab').length) {
            this.expenditureFormDisplayed = false;
            this.paintExpenditureForm();
        }

        //Remove edit button
        $('#user-edit').remove();
        //Modify footer buttons
        $('.modal-footer').empty();
        $('<input></input>').addClass('btn').attr('id','edit-accept').attr('value', 'Update').attr('type', 'button').appendTo('.modal-footer');
        $('<input></input>').addClass('btn btn-danger').attr('id','edit-cancel').attr('value', 'Cancel').attr('type', 'button').appendTo('.modal-footer');

        // Add new footer buttons listeners
        $('#edit-accept').click((function() {
            this.makeUpdateProfileRequest();
        }).bind(this));

        $('#edit-cancel').click((function() {
            // Paint user info
            this.display();
        }).bind(this));
    };

    /**
     * Paint basic user info
     */
    UserConfForm.prototype.paintUserInfo = function paintUserInfo() {
        var context;
        context = {
            'name': this.userProfile.getUsername(),
            'url': this.userProfile.getNotificationUrl()
        }
        if (!this.isOrg) {
            

            // Load the user info
            context['complete_name'] = this.userProfile.getCompleteName();
            context['roles'] = getRolesString(this);

            $.template('infoConfTemplate', $('#user_info_conf_template'));
        } else {
            $.template('infoConfTemplate', $('#org_info_conf_template'));
        }
        $.tmpl('infoConfTemplate', context).appendTo('#userinfo-tab');
    };

    /**
     * Paint user's tax addess
     */
    UserConfForm.prototype.paintAddressInfo = function paintAddressInfo() {
        var taxAddr = this.userProfile.getTaxAddress();

        // Create context for the template
        if (taxAddr) {
            var context = {
                'street': taxAddr.street,
                'postal': taxAddr.postal,
                'city': taxAddr.city,
                'province': taxAddr.province,
                'country': taxAddr.country
            };

            // Render the template
            $.template('addressConfTemplate', $('#address_conf_template'));
            $.tmpl('addressConfTemplate', context).appendTo('#taxaddr-tab');
        } else {
            var msg = 'No tax address defined in your profile. Edit your profile to provide one';
            MessageManager.showAlertInfo('No Tax Address', msg, $('#taxaddr-tab'));
        }
    };

    /**
     * Paint user's payment info
     */
    UserConfForm.prototype.paintPaymentInfo = function paintPaymentInfo() {
        var paymentInfo = this.userProfile.getPaymentInfo();

        // Create context for template
        if (paymentInfo) {
            var context = {
                'type': paymentInfo.type,
                'number': paymentInfo.number,
                'year': paymentInfo.expire_year,
                'month': paymentInfo.expire_month,
                'cvv2': paymentInfo.cvv2
            };

            // Render the template
            $.template('paymentInfoConfTemplate', $('#payment_info_conf_template'));
            $.tmpl('paymentInfoConfTemplate', context).appendTo('#paymentinfo-tab');
        } else {
            var msg = 'No payment info included in your profile. Edit your profile to provide it';
            MessageManager.showAlertInfo('No payment info', msg, $('#paymentinfo-tab'));
        }

    };

    /**
     * Paint user's expenditure limits
     */
    UserConfForm.prototype.paintExpenditureInfo = function paintExpenditureInfo() {
        var expenditureInfo = this.userProfile.getExpenditureInfo();

        if (!$.isEmptyObject(expenditureInfo)) {
            $.template('expenditureInfoTemplate', $('#expenditure_conf_template'));
            $.tmpl('expenditureInfoTemplate', expenditureInfo).appendTo('#expenditure-tab');
        } else {
            var msg = 'No expenditure limits included in your profile. Edit your profile to provide them';
            MessageManager.showAlertInfo('No expenditure limits', msg, $('#expenditure-tab'));
        }
    };

    /** 
     * Implements the method defined in ModalForm
     */
    UserConfForm.prototype.includeContents = function includeContents() {
        // Reset main button
        $('.modal-footer').empty();
        $('<a></a>').addClass('btn btn-basic').attr('data-dismiss','modal').attr('href', '#').text('Accept').appendTo('.modal-footer');

        // Paint user info
        this.paintUserInfo();
        this.paintAddressInfo();
        this.paintPaymentInfo();
        if($('#expenditure-tab').length) {
            this.paintExpenditureInfo();
        }
    };

    /**
     * Implements the method defined in ModalForm
     */
    UserConfForm.prototype.setListeners = function setListeners() {
        var editable = true;

        // Set edit listener
        if (this.isOrg) {
            // Check manager role
            if (USERPROFILE.getCurrentRoles().indexOf('manager') < 0) {
                editable = false;
            }
        }
        if (editable) {
            $('#user-edit').click((function() {
                this.displayEditProfileForm();
            }).bind(this));
        } else {
            $('#user-edit').remove();
        }

        $('#message').on('hidden', (function() {
            this.modalCreated = false;
            this.userFormDisplayed = false;
            this.addrFormDisplayed = false;
            this.paymentFormDisplayed = false;
            this.expenditureFormDisplayed = false;
        }.bind(this)));
    };

})();