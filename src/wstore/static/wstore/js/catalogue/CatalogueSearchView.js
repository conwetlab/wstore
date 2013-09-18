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

    var nextPage;

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

    getUserOfferings = function getUserOfferings (target, callback, endpoint, count) {

        var filter, offeringsPage;

        offeringsPage = $('#number-offerings').val();

        if (target == '#provided-tab') {
            filter = '?filter=provided&state=all';
        } else if (target == '#purchased-tab'){
            filter = '?filter=purchased';
        }
        if (count) {
            filter += '&action=count'
        } else {
            // Set number of offerings per page
            filter += '&limit=' + offeringsPage;
            // Set the first element
            filter += '&start=' + ((offeringsPage * (nextPage - 1)) + 1);

            if ($('#sorting').val() != '') {
                filter += '&sort=' + $('#sorting').val();
            }
        }
        $.ajax({
            type: "GET",
            url: endpoint + filter,
            dataType: 'json',
            success: function(response) {
                callback(target, response);
            },
            error: function(xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }

        })
    }

    paintProvidedOfferings = function paintProvidedOfferings (target, data) {

        $(target).empty();
        for (var i = 0; i < data.length; i++) {
            var offering_elem = new OfferingElement(data[i]);
            var labelClass = "label";
            var state = offering_elem.getState();
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
            }).click(paintOfferingDetails.bind(this, offering_elem, paintCatalogue, '#catalogue-container'));

            fillStarsRating(offering_elem.getRating(), templ.find('.stars-container'));
            templ.appendTo(target)
        }
        setFooter();
    };

    setNextPage = function setNextPage (nextPag) {
        nextPage = nextPag;
    };

})();
