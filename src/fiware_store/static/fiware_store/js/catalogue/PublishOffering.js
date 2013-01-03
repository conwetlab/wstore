(function(){

    var makePublishRequest = function makePublishRequest(offeringElement, markets) {
        var request = {};

        request.type = 'publish';
        request.markets = [];

        for (var i = 0; i < markets.length; i++) {
            if($('#' + markets[i].name).prop('checked')) {
                request.markets.push(markets[i].name);
            }
        };

        var csrfToken = $.cookie('csrftoken');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },  
            type: "PUT",
            url: EndpointManager.getEndpoint('APPLICATION_ENTRY', {
                'organization': offeringElement.getOrganization(),
                'name': offeringElement.getName(),
                'version': offeringElement.getVersion()
            }),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: function (response) {
                MessageManager.showMessage('Published', 'The application has been published');
                $('#catalogue-container').empty();
                paintCatalogue();
            },
            error: function (xhr) {
                var msg = 'Error: the server responds with code ' + xhr.status;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var paintPublishForm = function paintPublishForm (markets, offeringElement) {
        var formContent;
        MessageManager.showMessage('Publish offering','');

        if (markets.length > 0) {

            formContent = $('<div></div>');

            for (var i = 0; i < markets.length; i++) {
                $('<input></input>').attr('type', 'checkbox').attr('value', markets[i].name).attr('id', markets[i].name).appendTo(formContent);
                $('<label></label>').attr('for', markets[i].name).text(markets[i].name).appendTo(formContent);
            };

            formContent.appendTo('.modal-body');
            // Set listeners
            $('.modal-footer > .btn').click(function() {
                makePublishRequest(offeringElement, markets);
            })
        } else {
            $('<p></p>').text('No marketplaces where publish the offering have been registered');
        }
    };

    publishOffering = function publishOffering(offeringElement) {
        // Get marketplaces

        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('MARKET_COLLECTION'),
            dataType: 'json',
            success: function (response) {
                paintPublishForm(response, offeringElement);
            },
            error: function (xhr) {
                var msg = 'Error: the server responds with code ' + xhr.status;
                MessageManager.showMessage('Error', msg);
            }
        });

    };

})();
