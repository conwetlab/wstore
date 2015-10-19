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
     * User Form constructor
     */
    UserForm = function UserForm() {};

    /*
     * User form is a subclass of AdminForm
     */
    UserForm.prototype = new AdminForm('USERPROFILE_ENTRY', 'USERPROFILE_COLLECTION', $('#user_form_template'));
    UserForm.prototype.constructor = UserForm;

    /*
     * Implementation of validateFields abstract method, validate
     * User form and get form info
     */
    UserForm.prototype.validateFields = function validateFields() {
        var validation = {}, filled = 0, fields = 0, fullname_valid = true;
        var roles = [], tax_address = {}, credit_card = {};

        validation.valid = true;
        validation.data = {};

        // Get basic user info
        var firstname = $.trim($('input[id="id_first_name"]').val());
        var lastname = $.trim($('input[id="id_last_name"]').val());
        var username = $.trim($('input[id="id_user_name"]').val());
        var password = $.trim($('input[id="id_password1"]').val());
        var password_check = $.trim($('input[id="id_password2"]').val());
        // Check the full name
        if (!firstname || !lastname) {
            validation.valid = false;
            validation.msg = 'Missing required field';
            validation.errFields = [$('input[id="id_first_name"]').parent().parent()];
        } else {
            var name_re = new RegExp(/^[a-zA-Z\s]+$/);

            if (!name_re.test(firstname) || !name_re.test(lastname)) {
                fullname_valid = false;
                validation.valid = false;
                validation.msg = 'Invalid full name field';
                validation.errFields = [$('input[id="id_first_name"]').parent().parent()];
            } else {
                validation.data.first_name = firstname;
                validation.data.last_name = lastname;
            }
        }

        // Check the username
        if (!username) {
            if (validation.valid) {
                validation.valid = false;
                validation.msg = 'Missing required field';
                validation.errFields = [$('input[id="id_user_name"]').parent().parent()];
                
            } else {
                if (!fullname_valid) {
                    validation.msg += ' and missing required field';
                }
                validation.errFields.push($('input[id="id_user_name"]').parent().parent());
            }
            return validation;
        } else {
            var username_re = new RegExp(/^[\w.@+-]{5,}$/);

            if (!username_re.test(username)) {
                if (validation.valid) {
                    validation.valid = false;
                    validation.msg = 'Invalid username field';
                    validation.errFields = [$('input[id="id_user_name"]').parent().parent()];
                } else {
                    validation.msg += ' and invalid username field';
                    validation.errFields.push($('input[id="id_user_name"]').parent().parent());
                }
                return validation;
            } else {
                validation.data.username = username;
            }
        }

        // Get provider user info
        if ($('input[id="id_rol_provider"]').prop('checked')) {
            var notification_url = $.trim($('input[id="id_notification_url"]').val());
            var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);

            // Check the notification url
            if (notification_url && !urlReg.test(notification_url)) {
                validation.valid = false;
                validation.msg = 'Invalid URL format';
                validation.errFields = [$('input[id="id_notification_url"]').parent().parent()];
                return validation;
            } else {
                roles.push('provider');
                validation.data.notification_url = notification_url;
            }
        }

        // Get admin user info
        if ($('input[id="id_rol_admin"]').prop('checked')) {
            roles.push('admin');
        }

        validation.data.roles = roles;

        // Check the password
        var is_required = $('label[for="id_password1"]').text() == 'Password';
        
        $('input[id^="id_password"]').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            fields += 1;
        });
        
        if ((filled != 0 && filled != fields) || (filled == 0 && is_required)) {
            validation.valid = false;
            validation.msg = 'Missing required field';
            validation.errFields = [];
            $('input[id^="id_password"]').each(function() {
                if ($.trim($(this).val()).length == 0) {
                    filled += 1;
                    validation.errFields.push($(this).parent().parent());
                }
            });
            return validation;
        } else {
            if (password && password_check) {
                if (password.length < 5) {
                    validation.valid = false;
                    validation.msg = 'Invalid password field';
                    validation.errFields = [$('input[id="id_password1"]').parent().parent()];
                    return validation;
                }
                if (password != password_check) {
                    validation.valid = false;
                    validation.msg = 'Passwords do not match';
                    validation.errFields = [$('input[id="id_password2"]').parent().parent()];
                    return validation;
                }
                validation.data.password = password;
            }
        }

        filled = 0;
        fields = 0;

        // Get the credit card's input fields
        $('input[id^="id_card"]').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            fields += 1;
        });

        // Get the credit card's select fields
        $('select[id^="id_card"]').each(function() {
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
            $('input[id^="id_card"]').each(function() {
                if ($.trim($(this).val()).length == 0) {
                    filled += 1;
                    validation.errFields.push($(this).parent().parent());
                }
            });
            $('select[id^="id_card"]').each(function() {
                if ($.trim($(this).val()) == 0) {
                    filled += 1;
                    validation.errFields.push($(this).parent().parent());
                }
            });
            return validation;
        }

        if (filled != 0 && filled == fields) {
            credit_card.type = $.trim($('select[id="id_card_type"]').val());
            credit_card.number = $.trim($('input[id="id_card_number"]').val());
            credit_card.cvv2 = $.trim($('input[id="id_card_code"]').val());
            credit_card.expire_month = $.trim($('select[id="id_card_month"]').val());
            credit_card.expire_year = $.trim($('select[id="id_card_year"]').val());
            validation.data.payment_info = credit_card;
        }

        filled = 0;
        fields = 0;

        // Get the tax address
        $('input[id^="id_tax"]').each(function() {
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
            $('input[id^="id_tax"]').each(function() {
                if ($.trim($(this).val()).length == 0) {
                    filled += 1;
                    validation.errFields.push($(this).parent().parent());
                }
            });
            return validation;
        }

        if (filled != 0 && filled == fields) {
            tax_address.street = $.trim($('input[id="id_tax_street"]').val());
            tax_address.postal = $.trim($('input[id="id_tax_postcode"]').val());
            tax_address.city = $.trim($('input[id="id_tax_city"]').val());
            tax_address.province = $.trim($('input[id="id_tax_province"]').val())
            tax_address.country = $.trim($('input[id="id_tax_country"]').val());
            validation.data.tax_address = tax_address;
        }

        return validation;
    };

    /*
     * Display the User form and fill the User entry info for updating
     */
    UserForm.prototype.fillUserInfo = function fillUserInfo(user) {
        var credit_card, tax_address;

        // Paint the form
        this.paintForm();

        // Fill User entry info
        $('input[id="id_user_name"]').val(user.username).prop('readonly', true);
        $('input[id="id_first_name"]').val(user.first_name);
        $('input[id="id_last_name"]').val(user.last_name);

        if (user.roles.indexOf('provider') != -1) {
            $('input[id="id_rol_provider"]').prop('checked', true);
            $('input[id="id_notification_url"]').val(user.notification_url)
                .parent().parent().removeClass('hide');
        }

        if (user.roles.indexOf('admin') != -1) {
            $('input[id="id_rol_admin"]').prop('checked', true);
        }

        $('label[for="id_password1"]').text('Change Password');

        if (user.payment_info) {
            credit_card = user.payment_info;
            $('input[id="id_card_type"]').val(credit_card.type);
            $('input[id="id_card_number"]').val(credit_card.number);
            $('input[id="id_card_month"]').val(credit_card.expire_month);
            $('input[id="id_card_year"]').val(credit_card.expire_year);
            $('input[id="id_card_code"]').val(credit_card.cvv2);
        }

        if (user.tax_address) {
            tax_address = user.tax_address;
            $('input[id="id_tax_street"]').val(tax_address.street);
            $('input[id="id_tax_postcode"]').val(tax_address.postal);
            $('input[id="id_tax_city"]').val(tax_address.city);
            $('input[id="id_tax_province"]').val(tax_address.province);
            $('input[id="id_tax_country"]').val(tax_address.country);
        }

        // Change register button by an update button
        $('#elem-submit').val('Update').unbind('click').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.updateElementRequest({'username': user.username});
        }).bind(this));
    };

    /*
     * Implementation of fillListInfo abstract method, includes
     * Users in the list view
     */
    UserForm.prototype.fillListInfo = function fillListInfo(users) {
        $.template('elementTemplate', $('#element_template'));

        for (var i = 0; i < users.length; i++) {
            var editIcon;

            var template = $.tmpl('elementTemplate', {
                'name': users[i].username,
            });
            
            // Include edit icon
            editIcon = $('<i></i>').addClass('icon-edit').click((function(self, userEntry) {
                return function() {
                    self.fillUserInfo(userEntry);
                };
            })(this, users[i]));
            
            template.find('#elem-info').append(editIcon);

            // Include delete listener
            template.find('.delete').click((function(self, userEntry) {
                return function() {
                    var urlContext = {
                        'name': userEntry.username
                    }
                    self.mainClient.remove(self.elementInfoRequest.bind(self), urlContext);
                };
            })(this, users[i]));

            // Append entry
            template.appendTo('#table-list');
        }
    };

    /*
     * Implementation of setFormListeners abstract method, creates
     * extra listeners included in the form
     */
    UserForm.prototype.setFormListeners = function setFormListeners() {
        $('input[id="id_rol_provider"]').change(function() {
            if($(this).prop('checked')) {
                $('input[id="id_notification_url"]')
                    .parent().parent().removeClass('hide');
            } else {
                $('input[id="id_notification_url"]').val('')
                    .parent().parent().addClass('hide');
            }
        });
    };

})();