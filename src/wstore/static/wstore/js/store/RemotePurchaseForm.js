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

    notifyPurchaseEnd = function notifyPurchaseEnd(response) {
        // The window has been opened from an external source
        $('#back').remove();
        $('<input></input>').attr('id', 'back').addClass('btn btn-danger').attr('type', 'button').attr('value', 'End purchase').click(function() {
            window.location = response.client_redirection_uri;
        }).prependTo('#remote-container');
        $('#back').css('position', 'fixed').css('top', '51px').css('right', '180px');
    };

    getPriceStr = function getPriceStr(pricing) {
        var pricePlans;
        var priceStr = 'Free';

        if (pricing.price_plans && pricing.price_plans.length > 0) {
            var pricePlan = pricing.price_plans[0];

            if (pricePlan.price_components && pricePlan.price_components.length > 0) {
             // Check if it is a single payment
                if (pricePlan.price_components.length == 1) {
                    var component = pricePlan.price_components[0];
                    if (component.unit.toLowerCase() == 'single payment') {
                        priceStr = component.value;
                        if (component.currency == 'EUR') {
                            priceStr = priceStr + ' €';
                        } else {
                            priceStr = priceStr + ' £';
                        }
                    } else {
                        priceStr = 'View pricing';
                    }
                // Check if is a complex pricing
                } else {
                    priceStr = 'View pricing';
                }
            }
        }

        return priceStr;
    };

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

    closeMenuPainter = function closeMenuPainter() {
    };

    $(document).ready(function() {
        USERPROFILE = new UserProfile();
        USERPROFILE.fillUserInfo(refreshView);
    })
})();
