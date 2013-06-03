(function(){

    var makePublishRequest = function makePublishRequest(offeringElement, markets) {
        var request = {};

        request.marketplaces = [];

        for (var i = 0; i < markets.length; i++) {
            if($('#' + markets[i].name).prop('checked')) {
                request.marketplaces.push(markets[i].name);
            }
        };

        var csrfToken = $.cookie('csrftoken');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },  
            type: "POST",
            url: EndpointManager.getEndpoint('PUBLISH_ENTRY', {
                'organization': offeringElement.getOrganization(),
                'name': offeringElement.getName(),
                'version': offeringElement.getVersion()
            }),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: function (response) {
                MessageManager.showMessage('Published', 'The offering has been published');
                $('#catalogue-container').empty();
                offeringElement.setState('published');
                refreshDetailsView(offeringElement);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
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
                $('<label></label>').text(markets[i].host).appendTo(formContent);
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
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });

    };

})();
