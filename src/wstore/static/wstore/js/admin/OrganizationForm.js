(function() {

    var main = true;

    var makeCreateOrganizatonRequest = function makeCreateOrganizationRequest() {
        var organization = $.trim($('#org').val());

        if (organization != '') {
            var csrfToken = $.cookie('csrftoken');

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: 'POST',
                url: EndpointManager.getEndpoint('ORGANIZATION_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({'name': organization}),
                success: function (response) {
                    main = true; 
                    orgInfoRequest(paintOrganizations);
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            var msg = 'Missing required field';
            MessageManager.showMessage('Error', msg);
        }
    }

    paintOrganizations = function paintOrganizations(orgs) {
        $('#admin-container').empty();

        if (orgs.length > 0) {
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'Organizations'}).appendTo('#admin-container');

            for (var i = 0; i < orgs.length; i++) {
                $.template('elemTemplate', $('#element_template'));
                $.tmpl('elemTemplate', {'name': orgs[i]}).appendTo('#table-list');
            }
            $('.add').click(function() {
                main = false;
                painOrganizationForm();
            })
        } else {
            var msg = 'No organizations registered, you may want to register one'; 
            MessageManager.showAlertInfo('Organizations', msg);
        }
        $('#back').click(paintElementTable);
    }
    
    orgInfoRequest = function orgInfoRequest(callback, arg) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('ORGANIZATION_COLLECTION'),
            dataType: "json",
            success: function (response) {
                if (!arg) {
                    callback(response);
                } else {
                    callback(response, arg);
                }
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    }

    painOrganizationForm = function painOrganizationForm() {
        var form;

        $('#admin-container').empty();

        // Create the form
        $('<a></a>').text('Return').attr('id', 'back').appendTo('#admin-container');

        $('<h2></h2>').text('Organization').appendTo('#admin-container');
        form = $('<form></form>').addClass('form form-vertical').appendTo('#admin-container');
        $('<input></input>').attr('type', 'text').attr('id', 'org').attr('placeholder', 'Organization name').appendTo(form);
        $('<div></div>').addClass('btn btn-blue').attr('id', 'org-submit').text('Register').appendTo('#admin-container');

        // Set listeners
        $('#org-submit').click(makeCreateOrganizatonRequest);

        $('#back').click(function() {
            if (main) {
                paintElementTable();
            } else {
                orgInfoRequest(paintOrganizations);
                main = true;
            }
        })
    };
})();