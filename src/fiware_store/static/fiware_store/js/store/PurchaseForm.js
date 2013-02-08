
(function(){

    var makePurchaseRequest = function makePurchaseRequest(offeringElement) {
        var csrfToken = $.cookie('csrftoken');
        var request = {
            'offering': {
                'organization': offeringElement.getOrganization(),
                'name': offeringElement.getName(),
                'version': offeringElement.getVersion()
            },
            'organization_owned': $('#owned').prop('checked')
        }

        if ($('#tax_addr').val() != '') {
            request.tax_address = $('#tax_addr').val();
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
        var formContent = $('<div></div>');

        MessageManager.showMessage('Purchase offering', '');

        $('<label></label>').attr('for', 'tax_addr').text('Tax address').appendTo(formContent);
        $('<input></input>').attr('type', 'text').attr('id', 'tax_addr').attr('placeholder', 'Tax address').appendTo(formContent);

        $('<label></label>').attr('for', 'owned').text('Make the offering available to the whole organization').appendTo(formContent);
        $('<input></input>').attr('type', 'checkbox').attr('value', 'owned').attr('id', 'owned').appendTo(formContent);

        formContent.appendTo('.modal-body');
        // Set listeners
        $('.modal-footer > .btn').click(function() {
            makePurchaseRequest(offeringElement);
        });
    };

})();
