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

    var makeAddOrgUserRequest = function makeAddOrgUserRequest(org) {
        var user, roles = [];

        user = $.trim($('#user-org').val());

        if ($('#org-provider').prop('checked')) {
            roles.push('provider');
        }

        if ($('#org-customer').prop('checked')) {
            roles.push('customer');
        }

        if ($('#org-manager').prop('checked')) {
            roles.push('manager');
        }

        if (user && roles.length > 0) {
            var csrfToken = $.cookie('csrftoken');
            var request = {}

            request.user = user;
            request.roles = roles;
            $('#loading').removeClass('hide');    // Loading view when waiting for requests
            $('#loading').css('height', $(window).height() + 'px');
            $('#message').modal('hide');
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: 'POST',
                url: EndpointManager.getEndpoint('ORGANIZATION_USER_ENTRY', {
                    'org': org
                }),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    $('#loading').addClass('hide');
                    $('#message').modal('hide');
                    MessageManager.showMessage('Added', 'The user has been added');
                },
                error: function (xhr) {
                    $('#loading').addClass('hide');
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showAlertError('Error', 'Missing required field', $('#error'));
        }
    };

    displayOrganizationUsersForm = function displayOrganizationUsersForm(organization) {
        // Create the modal
        MessageManager.showMessage('Add User', '');
        $.template('orgUsersTemplate', $('#orgs_users_template'));
        $.tmpl('orgUsersTemplate').appendTo('.modal-body');

        $('.modal-footer > .btn').click(function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            makeAddOrgUserRequest(organization);
        });
    };

})();
