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

(function() {

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

    refreshView = function refreshView() {
        var offeringElement;
        var offDetailsView;

        // Create the offering Element
        offeringElement = new OfferingElement(OFFERING_INFO);
        offDetailsView = new CatalogueDetailsView(offeringElement, null, '#remote-container')

        offDetailsView.showView();

        // Remove unnecessary buttons and listeners
        $('#main-action').remove();
        $('h2:contains(Advanced operations)').remove();
        $('#advanced-op').remove();
        $('#back').remove();

        // Display purchase form
        offDetailsView.mainAction('Purchase');

        // Replace the event handler in order to remove created components
        $('#message').on('hidden', function(evnt) {
            evnt.stopPropagation();
            evnt.preventDefault();
            $('#message-container').empty();
        });
    }

    setFooter = function setFooter() {
        // Append the terms and conditions bar
        // Check if the bar is included
        if ($('footer').length > 0) {
            $('footer').remove();
        }
        // Create the new footer
        $.template('footerTemplate', $('#footer_template'));
        $.tmpl('footerTemplate').appendTo('body');
        $('footer').css('position', 'absolute').css('top', ($(document).height() - 30) + 'px');
    }

    $(window).resize(setFooter);

    $(document).ready(function() {
        USERPROFILE = new UserProfile();
        USERPROFILE.fillUserInfo()
    })
})();
