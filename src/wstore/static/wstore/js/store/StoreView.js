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

(function () {

    searchOfferings = function searchOfferings () {
        var text = $('#text-search').val();

        if (text != '') {
            $.ajax({
                type: "GET",
                url: EndpointManager.getEndpoint('SEARCH_ENTRY', {'text': text}),
                dataType: 'json',
                success: function(response) {
                    paintSearchView(response);
                },
                error: function(xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            });
        }
    };

    getOfferings = function getOfferings(endpoint, container, callback) {
         $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint(endpoint),
            dataType: 'json',
            success: function(response) {
                if (callback) {
                    callback(response);
                } else {
                    paintOfferings(response, container);
                }
            },
            error: function(xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }

        });
    };

    paintOfferings = function paintOfferings(data, container, backAct) {
        var action = paintHomePage;
        container.empty();

        if (backAct) {
            action=backAct;
        }

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
            }).appendTo(container).click(paintOfferingDetails.bind(this, offering_elem, action, '#home-container'));
        }
    }

    paintHomePage = function paintHomePage () {
        $('#home-container').empty();
        $.template('homePageTemplate', $('#home_page_template'));
        $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

        // Set search listeners
        $('#search').click(searchOfferings);
        $('#all').click(function() {
            getOfferings('OFFERING_COLLECTION', '', paintSearchView);
        })
        // Get initial offerings
        getOfferings('NEWEST_COLLECTION', $('#newest-container'));
        getOfferings('TOPRATED_COLLECTION', $('#top-rated-container'));
    };

    $(document).ready(paintHomePage);
})();
