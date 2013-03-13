
(function () {

    var getOfferings = function getOfferings() {
         $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('OFFERING_COLLECTION'),
            dataType: 'json',
            success: function(response) {
                paintOfferings(response);
            },
            error: function(xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }

        })
    }

    var paintOfferings = function paintOfferings(data) {
        for (var i = 0; i < data.length; i++) {
            var offering_elem = new OfferingElement(data[i]);
            var labelClass = "label";

            if (offering_elem.getState() == 'purchased') {
                labelClass += " label-success";
            } else if (offering_elem.getState() == 'published') {
                labelClass += " label-info";
            } else if (offering_elem.getState() == 'deleted') {
                labelClass += " label-important";
            }

            $.template('miniOfferingTemplate', $('#mini_offering_template'));
            $.tmpl('miniOfferingTemplate', {
                'name': offering_elem.getName(),
                'organization': offering_elem.getOrganization(),
                'logo': offering_elem.getLogo(),
                'state': offering_elem.getState(),
                'rating': offering_elem.getRating(),
                'description': offering_elem.getShortDescription(),
                'label_class': labelClass
            }).appendTo('#store-container').click(paintOfferingDetails.bind(this, offering_elem, paintHomePage, '#home-container'));
        }
    }

    paintHomePage = function paintHomePage () {
        $.template('homePageTemplate', $('#home_page_template'));
        $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

        getOfferings();
    };

    $(document).ready(paintHomePage);
})();
