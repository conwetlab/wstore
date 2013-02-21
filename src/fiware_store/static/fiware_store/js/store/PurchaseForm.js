
(function(){

    var displayed = false;

    var makePurchaseRequest = function makePurchaseRequest(offeringElement) {
        var csrfToken = $.cookie('csrftoken');
        var street, postal, city, country;

        var request = {
            'offering': {
                'organization': offeringElement.getOrganization(),
                'name': offeringElement.getName(),
                'version': offeringElement.getVersion()
            },
            'organization_owned': $('#owned').prop('checked')
        }

        if ($('#tax_addr').prop('checked')) {

            street = $('#street').val();
            postal = $('#postal').val();
            city = $('#city').val();
            country = $('#country').val();

            request.tax_address = {
                'street': street,
                'postal': postal,
                'city': city,
                'country': country
            }
        }

        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "POST",
            url: EndpointManager.getEndpoint('PURCHASE_COLLECTION'),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: function (response) {
                //Download resources
                downloadResources(response);
                //Refresh offering details view
                offeringElement.setState('purchased');
                refreshDetailsView(offeringElement);
            },
            error: function (xhr) {
                var msg = 'Error: the server responds with code ' + xhr.status;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var downloadResources = function downloadResources(data) {
        var resources = data.resources;
        for (var i = 0; i < resources.length; i++) {
            window.open(resources[i]);
        }
        window.open(data.bill);
    };

    purchaseOffering = function purchaseOffering(offeringElement) {

        MessageManager.showMessage('Purchase offering', '');

        $('<label></label>').attr('for', 'owned').text('Provide a different tax address').appendTo('.modal-body');
        $('<input></input>').attr('type', 'checkbox').attr('value', 'tax_addr').attr('id', 'tax_addr').appendTo('.modal-body');
        $('<div></div>').attr('id', 'addr_cont').appendTo('.modal-body');

        $('#tax_addr').change(function () {
            if(displayed) {
                $('#addr_cont').empty();
                displayed = false;
            } else {
                $.template('purchaseTemplate', $('#purchase_form_template'))
                $.tmpl('purchaseTemplate', {}).appendTo('#addr_cont')
                displayed = true;
            }
        });

        $('<label></label>').attr('for', 'owned').text('Make the offering available to the whole organization').appendTo('.modal-body');
        $('<input></input>').attr('type', 'checkbox').attr('value', 'owned').attr('id', 'owned').appendTo('.modal-body');

        // Set listeners
        $('.modal-footer > .btn').click(function() {
            makePurchaseRequest(offeringElement);
        });
    };

})();
