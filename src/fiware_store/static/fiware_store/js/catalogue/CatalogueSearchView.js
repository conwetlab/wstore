
(function () {

    getUserOfferings = function getUserOfferings (target) {

        var filter;

        if (target.hash == '#provided-tab') {
            filter = '?filter=provider&state=uploaded'; // TODO take into account published offerings
        } else if (target.hash == '#purchased-tab'){
            filter = '?filter=organization&state=purchased';
        }
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('APPLICATION_COLLECTION') + filter,
            dataType: 'json',
            success: function(response) {
                paintProvidedOfferings(target, response);
            },
            error: function(xhr) {
                var msg = 'Error the server responds with code ' + xhr.status;
                MessageManager.showMessage('Error', msg);
            }

        })
    }

    paintProvidedOfferings = function paintProvidedOfferings (target, data) {

        $(target.hash).empty();
        for (var i = 0; i < data.length; i++) {
            var offering_elem = new OfferingElement(data[i]);

            $.template('miniOfferingTemplate', $('#mini_offering_template'));
            $.tmpl('miniOfferingTemplate', {
                'name': offering_elem.getName(),
                'organization': offering_elem.getOrganization(),
                'logo': offering_elem.getLogo(),
                'state': offering_elem.getState(),
                'rating': offering_elem.getRating(),
                'description': offering_elem.getShortDescription()
            }).appendTo(target.hash).click(function () {
                paintOfferingDetails(offering_elem);
            });
        }
    };
})();
