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

        if (user && roles.length > 0) {
            var csrfToken = $.cookie('csrftoken');
            var request = {}

            request.user = user;
            request.roles = roles;
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
                    $('#message').modal('hide');
                    MessageManager.showMessage('Added', 'The user has been added');
                },
                error: function (xhr) {
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