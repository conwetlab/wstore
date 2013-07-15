(function() {

    var main = true;

    var makeCreateUnitRequest = function makeCreateUnitRequest() {
        var csrfToken = $.cookie('csrftoken');
        var name = $.trim($('#unit-name').val());

        if (name != '') {
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: 'POST',
                url: EndpointManager.getEndpoint('UNIT_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    'name': name,
                    'defined_model': $('#defined-model').val()
                }),
                success: function (response) {
                    unitsInfoRequest();
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            })
        } else {
            MessageManager.showMessage('Error', 'Name field is required');
        }
    };

    paintUnitForm = function paintUnitForm () {
        $('#admin-container').empty();

        $.template('unitFormTemplate', $('#unit_form_template'));
        $.tmpl('unitFormTemplate').appendTo('#admin-container');

        // Listener for back link
        $('#back').click(function() {
            if (main) {
                paintElementTable();
            } else {
                unitsInfoRequest();
            }
        });

        // Listener for submit
        $('#unit-submit').click(function() {
            makeCreateUnitRequest();
        });
    };

    var paintUnits = function paintUnits(units) {
        $('#admin-container').empty();

        if (units.length > 0) {
            // Create the units list
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'Units'}).appendTo('#admin-container');

            // Lister for new unit form
            $('.add').click(function() {
                main = false;
                paintUnitForm();
            });

            for (var i = 0; i < units.length; i++) {
                var row, column, div;

                // Append entry to units table
                $.template('elemTemplate', $('#element_template'));
                row = $.tmpl('elemTemplate', {'name': units[i].name, 'host': units[i].defined_model})
                row.appendTo('#table-list');
            }
        } else {
            var msg = 'No units registered, you may want to register one'; 
            MessageManager.showAlertInfo('Units', msg);
        }
        $('#back').click(paintElementTable);
    };

    unitsInfoRequest = function unitsInfoRequest() {
        main = true;

        // Make request asking for the registered units
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('UNIT_COLLECTION'),
            dataType: "json",
            success: function (response) {
                // Pint units list
                paintUnits(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };

})();