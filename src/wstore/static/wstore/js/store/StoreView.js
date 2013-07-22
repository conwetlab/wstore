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

    fillStarsRating = function fillStarsRating(rating, container) {
        // Fill rating stars

        for (var k = 0; k < 5; k ++) {
            var icon = $('<i></i>');

            if (rating == 0) {
                icon.addClass('icon-star-empty');
            } else if (rating > 0 && rating < 1) {
                icon.addClass('icon-star-half-empty blue-star');
                rating = 0;
            } else if (rating >= 1) {
                icon.addClass('icon-star blue-star');
                rating = rating - 1;
            }
            icon.appendTo(container);
        }
    };

    getOfferings = function getOfferings(endpoint, container, callback) {
         $.ajax({
            type: "GET",
            url: endpoint,
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
            var state = offering_elem.getState();
            var labelClass = "label";
            var stars, templ;

            if (state == 'rated') {
                state = 'purchased';
            }

            if (state == 'purchased') {
                labelClass += " label-success";
            } else if (state == 'published') {
                labelClass += " label-info";
            } else if (state == 'deleted') {
                labelClass += " label-important";
            }

            $.template('miniOfferingTemplate', $('#mini_offering_template'));
            templ = $.tmpl('miniOfferingTemplate', {
                'name': offering_elem.getName(),
                'organization': offering_elem.getOrganization(),
                'logo': offering_elem.getLogo(),
                'state': state,
                'rating': offering_elem.getRating(),
                'description': offering_elem.getShortDescription(),
                'label_class': labelClass
            }).click(paintOfferingDetails.bind(this, offering_elem, action, '#home-container'));

            fillStarsRating(offering_elem.getRating(), templ.find('.stars-container'));

            templ.appendTo(container)
        }
    }

    paintHomePage = function paintHomePage () {
        $('#home-container').empty();
        $.template('homePageTemplate', $('#home_page_template'));
        $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

        $('#search').click(function() {
            if ($.trim($('#text-search').val()) != '') {
                initSearchView('SEARCH_ENTRY');
            }
        });
        $('#all').click(function() {
            initSearchView('OFFERING_COLLECTION');
        })

        // Get initial offerings
        getOfferings(EndpointManager.getEndpoint('NEWEST_COLLECTION'), $('#newest-container'));
        getOfferings(EndpointManager.getEndpoint('TOPRATED_COLLECTION'), $('#top-rated-container'));
    };

    $(document).ready(paintHomePage);
})();
