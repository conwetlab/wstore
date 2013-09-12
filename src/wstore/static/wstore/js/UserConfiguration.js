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
     * Constructs the configuration form of an user profile
     * @param userProfile Object with user info
     */
    UserConfForm = function UserConfForm(userProfile) {
        this.userProfile = userProfile;
        this.modalCreated = false;
        this.userDisplayed = false;
        this.addrDisplayed = false;
        this.paymentDisplayed = false;
        this.userFormDisplayed = false;
        this.addrFormDisplayed = false;
        this.paymentFormDisplayed = false;
    };

    /**
     * Update the user profile with edit forms info
     */
    UserConfForm.prototype.makeUpdateProfileRequest = function makeUpdateProfileRequest() {
        var filled, msg, error = false;
        var request = {};

        // Load user info
        request.username = this.userProfile.getUsername();
        request.complete_name = $.trim($('#complete-name').val());
        request.organization = $('#org-name').text();
        request.roles = []


        if ($('#admin').prop('checked')) {
            request.roles.push('admin');
        }

        if ($('#provider').prop('checked')) {
            request.roles.push('provider');
        }

        // Load tax address
        filled = 0;

        $('.tax-input').each(function(evnt) {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
        });

        // If any field is filled all fields must be filled
        if (filled != 0) {
            if (filled != 3) {
                error = true;
                msg = 'If a field of tax address is filled all fields must be filled';
            } else {
                request.tax_address = {
                    'street': $.trim($('#street').val()),
                    'postal': $.trim($('#postal').val()),
                    'city': $.trim($('#city').val()),
                    'country': $.trim($('#country').val())
                };
            }
        }

        // Load Payment info
        /*filled = 0;

        $('.payment-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
        });

        // If any field is filled all fields must be filled
        if (filled != 0) {
            if (filled != 5) {
                error = true;
                msg = 'If a field of payment info is filed all fields must be filled';
            } else {
                request.payment_info = {
                    'type': $('#type').val(),
                    'number': $.trim($('#number').val()),
                    'expire_month': $('#expire-month').val(),
                    'expire_year': $.trim($('#expire-year').val()),
                    'cvv2': $.trim($('#cvv2').val())
                };
            }
        }*/

        // If not error occurred
        if (!error) {
            this.userProfile.updateProfile(request, this.display.bind(this));
        } else {
            MessageManager.showAlertError('Error', msg, $('#error-message'));
            $('#error-message .close').remove();
        }
    };

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
                'username': this.userProfile.getUsername(),
                'complete_name': this.userProfile.getCompleteName()
            }

            $.template('userInfoFormTemplate', $('#user_info_form_template'));
            $.tmpl('userInfoFormTemplate', context).appendTo('#main-info');

            if (this.userProfile.getUserRoles().indexOf('admin') != -1) {
                $('#admin').prop('checked', true);
            }
            if (this.userProfile.getCurrentRoles().indexOf('provider') != -1) {
                $('#provider').prop('checked', true);
            }
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
                    'country': taxAddr.country
                };
            } else {
                context = {
                    'street': '',
                    'postal': '',
                    'city': '',
                    'country': ''
                };
            }

            $.template('addressConfFormTemplate', $('#address_conf_form_template'));
            $.tmpl('addressConfFormTemplate', context).appendTo('#taxaddr-tab');
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
        var context, roles = '';
        var currentRoles = this.userProfile.getCurrentRoles();

        this.userDisplayed = true;

        for (var i = 0; i < currentRoles.length; i++) {
            roles += (' ' + currentRoles[i] + ',');
        }

        // Load the user info
        context = {
                'username': this.userProfile.getUsername(),
                'complete_name': this.userProfile.getCompleteName(),
                'roles': roles,
                'organization': this.userProfile.getCurrentOrganization()
        }

        $.template('userInfoConfTemplate', $('#user_info_conf_template'));
        $.tmpl('userInfoConfTemplate', context).appendTo('#userinfo-tab');

        // Check if is needed to include a select for organizations change
        if (!$('#oil-nav').length > 0) {
            var orgsSelect = $('<select></select>').attr('id', 'org-select');
            var organizations = this.userProfile.getOrganizations();

            // Load organizations info
            for (var i = 0; i < organizations.length; i++) {
                var org;
                org = $('<option></option>').attr('value', organizations[i].name);
                org.text(organizations[i].name);
                org.appendTo(orgsSelect);
            }

            orgsSelect.appendTo('#org-info');

            // Set initial value for the org select
            orgsSelect.val(this.userProfile.getCurrentOrganization());

            // Set listener for organization change
            orgsSelect.change((function() {
                this.userProfile.changeOrganization($('#org-select').val(), this.display.bind(this));
            }).bind(this));
        }

    };

    /**
     * Paint user's tax addess
     */
    UserConfForm.prototype.paintAddressInfo = function paintAddressInfo() {
        var taxAddr = this.userProfile.getTaxAddress();

        this.addrDisplayed = true;

        // Create context for the template
        if (taxAddr) {
            var context = {
                'street': taxAddr.street,
                'postal': taxAddr.postal,
                'city': taxAddr.city,
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

        this.paymentDisplayed = true;

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
     * Shows the form with user info configuration
     */
    UserConfForm.prototype.display = function display() {
        if (!this.modalCreated) {
            MessageManager.showMessage('Configuration', '');
            this.modalCreated = true;
        }

        $('.modal-body').empty();

        // Append the template
        $.template('userConfTemplate', $('#user_conf_template'));
        $.tmpl('userConfTemplate').appendTo('.modal-body');

        // Reset main button
        $('.modal-footer').empty();
        $('<a></a>').addClass('btn btn-basic').attr('data-dismiss','modal').attr('href', '#').text('Accept').appendTo('.modal-footer');

        // Paint user info
        this.paintUserInfo();
        this.paintAddressInfo();
        this.paintPaymentInfo();

        // Set edit listener
        $('#user-edit').click((function() {
            this.displayEditProfileForm();
        }).bind(this));

        $('#message').on('hidden', (function() {
            this.modalCreated = false;
            this.userFormDisplayed = false;
            this.addrFormDisplayed = false;
            this.paymentFormDisplayed = false;
        }.bind(this)));
    };

})();

includeFilabOrgMenu = function includeFilabOrgMenu() {
    var organizations = USERPROFILE.getOrganizations();
    $('.dropdown-submenu').remove();

    // Include switch sesion menu if the user belong to
    // any organization
    if (organizations.length > 1) {
        var ul;
        var leftMenu = $('<li></li>').addClass('dropdown-submenu pull-left');
        $('<a></a>').text('Switch session').appendTo(leftMenu);
        $('<i></i>').addClass('icon-caret-right').appendTo(leftMenu);

        ul = $('<ul></ul>').addClass('dropdown-menu dropdown-menu-header').appendTo(leftMenu);

        for (var i = 0; i < organizations.length; i++) {
            if (organizations[i].name != USERPROFILE.getCurrentOrganization()) {
                var li = $('<li></li>');
                var a = $('<a></a>').text(organizations[i].name).attr('data-placement','left').attr('data-toggle', 'tooltip');
                a.appendTo(li);

                if (organizations[i].name == USERPROFILE.getUsername()) {
                    a.text(USERPROFILE.getCompleteName());
                    a.prepend($('<img></img>').attr('src', '/static/oil/img/user.png'));
                    ul.prepend(li);
                } else {
                    a.prepend($('<img></img>').attr('src', '/static/oil/img/group.png'));
                    ul.append(li);
                }
                // Set listeners for organizations switching
                li.click((function(org) {
                    return function() {
                        USERPROFILE.changeOrganization(org, includeFilabOrgMenu);
                    }
                })(organizations[i].name));
            }
        }

        ul.css('display', 'none');
        ul.css('position', 'absolute');
        ul.css('top', '10px');
        ul.css('right', '157px');

        leftMenu.on('mouseover', function() {
            ul.css('display', 'block');
        });

        leftMenu.on('mouseout', function() {
            ul.css('display', 'none');
        });

        $('#settings-menu').prepend(leftMenu);

        // Set username
        if (USERPROFILE.getCurrentOrganization() == USERPROFILE.getUsername()) {
            $('.oil-usr-icon').attr('src', '/static/oil/img/user.png');
            $('#oil-usr').text(USERPROFILE.getCompleteName());
        } else {
            $('.oil-usr-icon').attr('src', '/static/oil/img/group.png');
            $('#oil-usr').text(USERPROFILE.getCurrentOrganization());
        }
    }
};

$(document).ready(function() {
    var userForm;

    USERPROFILE = new UserProfile()

    if ($('#oil-nav').length > 0) {
        USERPROFILE.fillUserInfo(includeFilabOrgMenu);
    } else {
        USERPROFILE.fillUserInfo();
    }

    
    userForm = new UserConfForm(USERPROFILE);

    $('#conf-link').click(function() {
        userForm.display();
    });
});
