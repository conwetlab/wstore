(function() {

    var userDisplayed;
    var addrDisplayed;
    var paymentDisplayed;

    var userFormDisplayed;
    var addrFormDisplayed;
    var paymentFormDisplayed;

    var makeUpdateProfileRequest = function makeUpdateProfileRequest(username) {
        var filled, msg, error = false;
        var request = {};

        // Load user info
        request.username = username;
        request.first_name = $.trim($('#first-name').val());
        request.last_name = $.trim($('#last-name').val());
        request.organization = $('#org-name').text();
        request.roles = []

        if ($('#admin').prop('checked')) {
            request.roles.push('admin');
        }

        if ($('#provider').prop('checked')) {
            request.roles.push('provider');
        }

        if (request.first_name == '' || request.last_name == '') {
            error = true;
            msg = 'Missing required field';
        }

        // Load tax address
        filled = 0;

        $('.tax-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
        });

        // If any field is filled all fields must be filled
        if (filled != 0) {
            if (filled != 4) {
                error = true;
                msg = 'If a field of tax address is filed all fields must be filled';
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
        filled = 0;

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
        }

        // If not error occurred
        if (!error) {
            var csrfToken = $.cookie('csrftoken');

            // Make PUT request
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: 'PUT',
                url: EndpointManager.getEndpoint('USERPROFILE_ENTRY', {'username': username}),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    // Reset main button
                    $('.modal-footer').empty();
                    $('<a></a>').addClass('btn btn-basic').attr('data-dismiss','modal').attr('href', '#').text('Accept').appendTo('.modal-footer');
                    // Update user info
                    getUserInfo();
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showMessage('Error', msg);
        }
    };

    var paintUserConf = function painUserConf(userInfo) {
        var taxAddr, paymentInfo;

        userDisplayed = false;
        addrDisplayed = false;
        paymentDisplayed = false;

        $('.modal-body').empty();

        // Append the template
        $.template('userConfTemplate', $('#user_conf_template'));
        $.tmpl('userConfTemplate').appendTo('.modal-body');

        // Paint user info
        paintUserInfo(userInfo);

        // Check is exists a tax address
        if (userInfo.tax_address) {
            taxAddr = userInfo.tax_address;
        } else {
            taxAddr = false;
        }

        paintAddressInfo(taxAddr);

        // Check if exists payment info
        if (userInfo.payment_info) {
            paymentInfo = userInfo.payment_info;
        } else {
            paymentInfo = false;
        }

        paintPaymentInfo(paymentInfo);

        // Set edit listener
        $('#user-edit').click(function() {
            displayEditProfileForm(userInfo);
        })
    };

    var displayEditProfileForm = function displayEditProfileForm(userInfo) {

        userFormDisplayed = false;
        addrFormDisplayed = false;
        paymentFormDisplayed = false;

        paintEditUserInfoForm(userInfo);
        paintEditTaxAddrForm(userInfo.tax_address);
        paintEditPaymentInfoForm(userInfo.payment_info);

        //Remove edit button
        $('#user-edit').remove();
        //Modify footer buttons
        $('.modal-footer').empty();
        $('<input></input>').addClass('btn').attr('id','edit-accept').attr('value', 'Update').attr('type', 'button').appendTo('.modal-footer');
        $('<input></input>').addClass('btn btn-danger').attr('id','edit-cancel').attr('value', 'Cancel').attr('type', 'button').appendTo('.modal-footer');

        // Add new footer buttons listeners
        $('#edit-accept').click(function() {
            makeUpdateProfileRequest(userInfo.username);
        });

        $('#edit-cancel').click(function() {
            // Reset main button
            $('.modal-footer').empty();
            $('<a></a>').addClass('btn btn-basic').attr('data-dismiss','modal').attr('href', '#').text('Accept').appendTo('.modal-footer');
            // Paint user info
            paintUserConf(userInfo);
        });
    };

    var paintEditUserInfoForm = function paintEditUserInfoForm(userInfo) {
        if (!userFormDisplayed) {
            var context;

            userFormDisplayed = true;

            $('#main-info').empty();

            // Load the user info
            context = {
                'username': userInfo.username,
                'first_name': userInfo.first_name,
                'last_name': userInfo.last_name,
            }

            $.template('userInfoFormTemplate', $('#user_info_form_template'));
            $.tmpl('userInfoFormTemplate', context).appendTo('#main-info');

            if (userInfo.roles.indexOf('admin') != -1) {
                $('#admin').prop('checked', true);
            }
            if (userInfo.roles.indexOf('provider') != -1) {
                $('#provider').prop('checked', true);
            }
        }
    };

    var paintEditTaxAddrForm = function paintEditTaxAddr(taxAddr) {
        if (!addrFormDisplayed) {
            var context;

            addrFormDisplayed = true;

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

    var paintEditPaymentInfoForm = function paintEditPaymentInfo(paymentInfo) {
        if (!paymentFormDisplayed) {
            var context, month, type;

            paymentFormDisplayed = true;

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

    var paintUserInfo = function paintUserInfo(userInfo) {
        if (!userDisplayed) {
            var context, roles = '';
            userDisplayed = true;

            for (var i = 0; i < userInfo.roles.length; i++) {
                roles += (' ' + userInfo.roles[i] + ',');
            }

            // Load the user info
            context = {
                'username': userInfo.username,
                'first_name': userInfo.first_name,
                'last_name': userInfo.last_name,
                'roles': roles,
                'organization': userInfo.organization
            }

            $.template('userInfoConfTemplate', $('#user_info_conf_template'));
            $.tmpl('userInfoConfTemplate', context).appendTo('#userinfo-tab');
        }
    };

    var paintAddressInfo = function paintAddressInfo(taxAddr) {
        if(!addrDisplayed) {
            addrDisplayed = true;

            if (taxAddr) {
                var context = {
                    'street': taxAddr.street,
                    'postal': taxAddr.postal,
                    'city': taxAddr.city,
                    'country': taxAddr.country
                };

                $.template('addressConfTemplate', $('#address_conf_template'));
                $.tmpl('addressConfTemplate', context).appendTo('#taxaddr-tab');
            } else {
                var msg = 'No tax address defined in your profile. Edit your profile to provide one';
                MessageManager.showAlertInfo('No Tax Address', msg, $('#taxaddr-tab'));
            }
        }
    };

    var paintPaymentInfo = function paintPaymentInfo(paymentInfo) {
        if (!paymentDisplayed) {
            paymentDisplayed = true;

            if (paymentInfo) {
                var context = {
                    'type': paymentInfo.type,
                    'number': paymentInfo.number,
                    'year': paymentInfo.expire_year,
                    'month': paymentInfo.expire_month,
                    'cvv2': paymentInfo.cvv2
                };

                $.template('paymentInfoConfTemplate', $('#payment_info_conf_template'));
                $.tmpl('paymentInfoConfTemplate', context).appendTo('#paymentinfo-tab');
            } else {
                var msg = 'No payment info included in your profile. Edit your profile to provide it';
                MessageManager.showAlertInfo('No payment info', msg, $('#paymentinfo-tab'));
            }
        }
    };

    var getUserInfo = function getUserInfo() {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('USERPROFILE_ENTRY', {'username': USERNAME}),
            dataType: "json",
            success: function (response) {
                paintUserConf(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };

    $(document).ready(function() {
        $('#conf-link').click(function() {
            MessageManager.showMessage('Configuration', '');
            getUserInfo();
        });
    });
})();