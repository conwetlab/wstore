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

    var getPriceStr = function getPriceStr(pricing) {
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

    paintProvidedOfferings = function paintProvidedOfferings (target, data) {

        $(target).empty();
        for (var i = 0; i < data.length; i++) {
            var offering_elem = new OfferingElement(data[i]);
            var offDetailsView = new CatalogueDetailsView(offering_elem, paintCatalogue, '#catalogue-container');
            var labelClass = "label";
            var labelValue = offering_elem.getState();
            var stars, templ, priceStr;

            // Append Price and button if necessary
            $.template('miniOfferingTemplate', $('#mini_offering_template'));
            templ = $.tmpl('miniOfferingTemplate', {
                'name': offering_elem.getName(),
                'organization': offering_elem.getOrganization(),
                'logo': offering_elem.getLogo(),
                'description': offering_elem.getShortDescription()
            }).click((function(off) {
                return function() {
                    off.showView();
                }
            })(offDetailsView));

            // Include the gradient if needed
            if (offering_elem.getName().length > 18) {
                var spanDeg; 
                $('<span></span>').addClass('txt-gradient').appendTo(templ.find('h2'));
            }

            fillStarsRating(offering_elem.getRating(), templ.find('.stars-container'));

            priceStr = getPriceStr(offering_elem.getPricing())
            // Append button
            if ((USERPROFILE.getCurrentOrganization() != offering_elem.getOrganization()) 
                    && (labelValue == 'published')) {
                var padding = '18px';
                var text = priceStr;
                var buttonClass = "btn btn-success";

                if (priceStr != 'Free') {
                    padding = '13px';
                    buttonClass = "btn btn-blue";
                }

                if (priceStr == 'View pricing') {
                    text = 'Purchase';
                }
                $('<button></button>').addClass(buttonClass + ' mini-off-btn').text(text).click((function(off) {
                    return function() {
                        off.showView();
                        off.mainAction('Purchase');
                    }
                })(offDetailsView)).css('padding-left', padding).appendTo(templ.find('.offering-meta'));
            } else {
                var span = $('<span></span>').addClass('mini-off-price').text(priceStr);
                if (priceStr == 'Free') {
                    span.css('color', 'green');
                }
                span.appendTo(templ.find('.offering-meta'));
            }
                
            if (labelValue != 'published') {
                var label = $('<span></span>');
                if (labelValue == 'purchased' || labelValue == 'rated') {
                    labelClass += " label-success";
                    labelValue = 'purchased';
                } else if (labelValue == 'deleted') {
                    labelClass += " label-important";
                }
                label.addClass(labelClass).text(labelValue);
                templ.find('.off-org-name').before(label);
                templ.find('.off-org-name').css('width', '126px')
                templ.find('.off-org-name').css('left', '78px');
            }
            templ.appendTo(target)
        }
        setFooter();
    };

    setNextPage = function setNextPage (nextPag) {
        nextPage = nextPag;
    };

})();
