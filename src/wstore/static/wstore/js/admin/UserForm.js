(function() {

    var main = true;

    var fillUserInfo = function fillUserInfo(userInfo) {
        var credit_card, tax_address;

        $('#user-name').val(userInfo.username).prop('readonly', true);
        $('#first-name').val(userInfo.first_name);
        $('#last-name').val(userInfo.last_name);

        if (userInfo.roles.indexOf('provider') != -1) {
            $('#provider').prop('checked', true);
        }

        if (userInfo.roles.indexOf('admin') != -1) {
            $('#admin').prop('checked', true);
        }
        $('#organization').val(userInfo.organization).prop('disabled', true);

        if (userInfo.payment_info) {
            credit_card = userInfo.payment_info
            $('#type').val(credit_card.type);
            $('#number').val(credit_card.number);
            $('#expire-month').val(credit_card.expire_month);
            $('#expire-year').val(credit_card.expire_year);
            $('#cvv2').val(credit_card.cvv2);
        }

        if (userInfo.tax_address) {
            tax_address = userInfo.tax_address;
            $('#street').val(tax_address.street);
            $('#postal').val(tax_address.postal);
            $('#city').val(tax_address.city);
            $('#country').val(tax_address.country);
        }
        $('#user-submit').text('Update');
    };

    var paintUsers = function paintUsers(users) {

        $('#admin-container').empty();

        if (users.length > 0) {
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'User profile'}).appendTo('#admin-container');

            for (var i = 0; i < users.length; i++) {
                var row, column, div;
                $.template('elemTemplate', $('#element_template'));
                row = $.tmpl('elemTemplate', {'name': users[i].username})
                row.appendTo('#table-list');

                column = $('<td></td>');
                div = $('<div></div>').addClass('update').appendTo(column);
                $('<i></i>').addClass('icon-edit').appendTo(div);
                column.appendTo(row);

                div.click((function(user) {
                    return function() {
                        paintUserForm(user);
                    }
                })(users[i]));
            }

            $('#back').click(paintElementTable);

            $('.add').click(function () {
                main = false;
                paintUserForm();
            });
            $('.delete').click(function (event) {
                var clicked_elem = event.target;
                makeRemoveRequest(clicked_elem, endpoint, title)
            });
        }
    };

    var makeProfileRequest = function makeProfileRequest(endpoint, method) {
        var username, firstName, lastName, organization;
        var roles = [];
        var request = {};
        var filled = 0, inputs = 0, error = false;

        // Get basic user info
        username = $.trim($('#user-name').val());
        firstName = $.trim($('#first-name').val());
        lastName = $.trim($('#last-name').val());

        if (method == 'POST' || ($('#passwd-input').length > 0)) {
            var passwd, passConf;

            // If is creating a new user the password is required
            passwd = $.trim($('#passwd-input').val());
            passConf = $.trim($('#passwd-conf').val());

            if (passwd == '' || passConf == '') {
                error = true;
                msg = 'Missing required password field';
            } else if(passwd != passConf) {
                error = true;
                msg = 'The password and password confirm do not match';
            } else {
                request.password = passwd;
            }
        } 

        if ($('#provider').prop('checked')) {
            roles.push('provider');
        }
        if ($('#admin').prop('checked')) {
            roles.push('admin');
        }

        organization = $('#organization').val();

        if (!username || !firstName || !lastName || !organization) {
            error = true
            msg = 'Missing a required field';
        }
        request.username = username;
        request.first_name = firstName;
        request.last_name = lastName;
        request.organization = organization;
        request.roles = roles;

        // Get the tax address
        $('.addr-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            inputs += 1;
        });

        // The tax address is not required; however, if it is wanted to
        // provide it all fields are required.
        if (filled != 0 && filled == inputs) {
            var taxAddr = {
                'street': $.trim($('#street').val()),
                'postal': $.trim($('#postal').val()),
                'city': $.trim($('#city').val()),
                'country': $.trim($('#country').val())
            }
            request.tax_address = taxAddr;
        } else if (filled != 0) {
            error = true;
            msg = 'To provide a tax address all fields are required';
        }

        filled = 0;
        inputs = 0;
        // The credit card info is not required; however, if it is wanted to
        // provide it all fields are required.
        $('.credit-input').each(function() {
            if ($.trim($(this).val()).length != 0) {
                filled += 1;
            }
            inputs += 1;
        });

        if (filled != 0 && filled == inputs && $('#type').val() != 0 && $('#expire-month').val() != 0) {
            var creditCard = {
                'type': $('#type').val(),
                'number': $.trim($('#number').val()),
                'expire_month': $('#expire-month').val(),
                'expire_year': $.trim($('#expire-year').val()),
                'cvv2': $.trim($('#cvv2').val())
            }
            request.payment_info = creditCard;
        } else if (filled != 0) {
            error = true;
            msg = 'To provide a credit card all fields are required';
        }

        // if all the info provided is correct make the request
        if (!error) {
            var csrfToken = $.cookie('csrftoken');

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: method,
                url: endpoint,
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    userInfoRequest();
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showMessage('Error', msg);
        }
    };

    var paintCompleteUserForm = function paintCompleteUserForm(orgs, user) {
        $('#admin-container').empty();
        $.template('userTemplate', $('#user_form_template')); // Create the template
        $.tmpl('userTemplate').appendTo("#admin-container"); // Render and append the template

        for (var i = 0; i < orgs.length; i++) {
            $('<option></option>').val(orgs[i]).text(orgs[i]).appendTo('#organization');
        }

        if (user) {
            var checkPass;

            // Include the user info
            fillUserInfo(user);

            // Add the password inputs
            $('<p></p>').text('Change password').appendTo('#passwd');
            checkPass =$('<input></input>').attr('type', 'checkbox').attr('id', 'passwd-check').appendTo('#passwd');
            $('<div></div>').attr('id', 'passwd-cont').appendTo('#passwd');
            checkPass.change(function() {
                // If the fields are no displayed
                if ($('#passwd-input').length == 0){
                    $('<input></input>').attr('type', 'password').attr('id', 'passwd-input').attr('placeholder', 'Password').appendTo('#passwd-cont');
                    $('<input></input>').attr('type', 'password').attr('id', 'passwd-conf').attr('placeholder', 'Confirm password').appendTo('#passwd-cont');
                } else {
                    $('#passwd-cont').empty();
                }
            })
            $('#back').click(userInfoRequest);
            $('#user-submit').click(function(event) {
                var endpoint, method;

                if ($.trim($('#user-name').val()).length != 0) {
                    endpoint = EndpointManager.getEndpoint('USERPROFILE_ENTRY', {'username': user.username});
                    method = 'PUT';
                } else {
                    endpoint = EndpointManager.getEndpoint('USERPROFILE_COLLECTION');
                    method = 'POST';
                }
                makeProfileRequest(endpoint, method);
            });
        } else {
            // Add the password inputs
            $('<p></p>').text('Password').appendTo('#passwd');
            $('<input></input>').attr('type', 'password').attr('id', 'passwd-input').attr('placeholder', 'Password').appendTo('#passwd');
            $('<input></input>').attr('type', 'password').attr('id', 'passwd-conf').attr('placeholder', 'Confirm password').appendTo('#passwd');

            // Check the previous page to return
            if (main){
                $('#back').click(paintElementTable);
            } else {
                $('#back').click(userInfoRequest);
                main = true;
            }

            // Add the submit handler
            $('#user-submit').click(function() {
                var endpoint = EndpointManager.getEndpoint('USERPROFILE_COLLECTION');
                makeProfileRequest(endpoint, 'POST');
            });
        }
    }

    userInfoRequest = function userInfoRequest() {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('USERPROFILE_COLLECTION'),
            dataType: "json",
            success: function (response) {
                paintUsers(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    paintUserForm = function paintUserForm(user) {
        if (!user) {
            orgInfoRequest(paintCompleteUserForm);
        } else {
            orgInfoRequest(paintCompleteUserForm, user);
        }
    };
})();