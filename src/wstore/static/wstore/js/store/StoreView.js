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

    var searchView;
    var evntAllowed = true;
    var mpainter;

    refreshView = function refreshView() {
        $('home-container').empty();
        paintHomePage();
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

    getOfferings = function getOfferings(endpoint, container, callback) {
         $.ajax({
            type: "GET",
            url: endpoint,
            dataType: 'json',
            success: function(response) {
                if (callback) {
                    callback(response);
                } else {
                    paintOfferings(response, container, true);
                }
            },
            error: function(xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }

        });
    };

    getPriceStr = function getPriceStr(pricing) {
        var pricePlans;
        var priceStr = 'Free';

        if (pricing.price_plans && pricing.price_plans.length > 0) {
            if (pricing.price_plans.length == 1) {
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
            } else {
                priceStr = 'View pricing';
            }
        }

        return priceStr;
    };

    paintOfferings = function paintOfferings(data, container, toEmpty, backAct) {
        var action = function() {
            paintHomePage();
            mpainter.increase();
        }

        if (toEmpty) {
            container.empty();
        }

        if (backAct) {
            action = function() {
                backAct();
                mpainter.increase();
            }
        }

        for (var i = 0; i < data.length; i++) {
            var offering_elem = new OfferingElement(data[i]);
            var offDetailsView = new CatalogueDetailsView(offering_elem, action, '#home-container');
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

            templ.appendTo(container)
        }
        if (!evntAllowed) {
            evntAllowed = true;
        }
    }

    setMenuHandlers = function setMenuHandlers() {

        $('#menu-first-text').off('click');
        $('#menu-second-text').off('click');
        $('#menu-third-text').off('click');

        $('#menu-first-text').click(function() {
            if ($('.detailed-info').length) {
                $('#home-container').empty()
            }
            searchView.setTitle('Services');
            searchView.initSearchView('SEARCH_TAG_ENTRY', 'service');
        });
        $('#menu-second-text').click(function() {
            if ($('.detailed-info').length) {
                $('#home-container').empty()
            }
            searchView.setTitle('Datasets');
            searchView.initSearchView('SEARCH_TAG_ENTRY', 'dataset');
        });
        $('#menu-third-text').click(function() {
            if ($('.detailed-info').length) {
                $('#home-container').empty()
            }
            searchView.setTitle('Widgets / Mashups');
            searchView.initSearchView('SEARCH_TAG_ENTRY', 'widget');
        });
    };
    
    paintHomePage = function paintHomePage () {
        // Create search view object
        searchView = new StoreSearchView();

        $('#home-container').empty();
        $.template('homePageTemplate', $('#home_page_template'));
        $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

        $('#search').click(function() {
            if ($.trim($('#text-search').val()) != '') {
                searchView.setTitle('Offerings');
                searchView.initSearchView('SEARCH_ENTRY');
            }
        });

        // Set listener for enter key
        $('#text-search').keypress(function(e) {
            if (e.which == 13 && $.trim($(this).val()) != '') {
                e.preventDefault();
                e.stopPropagation();
                searchView.setTitle('Offerings');
                searchView.initSearchView('SEARCH_ENTRY');
            }
        });

        $('#all').click(function() {
            searchView.setTitle('Offerings');
            searchView.initSearchView('OFFERING_COLLECTION');
        })

        // Bind menu handlers
        if (!mpainter)  {
            mpainter = new MenuPainter(setMenuHandlers);
        }
        // Get initial offerings
        calculatePositions();
        getOfferings(EndpointManager.getEndpoint('NEWEST_COLLECTION'), $('#newest-container'));
        getOfferings(EndpointManager.getEndpoint('TOPRATED_COLLECTION'), $('#top-rated-container'));
    };

    closeMenuPainter = function closeMenuPainter() {
        mpainter.decrease();
    };

    calculatePositions = function calculatePositions(evnt) {
        var position;
        var filabInt = $('#oil-nav').length > 0;

        if ($('.search-container').length > 0) {
            var offset, scrollContPos;
            // Refresh the search view in order to adapt the page length
            // to the new window length.
            if (evnt && evntAllowed) {
                evntAllowed = false; // Avoid to handle the event until the previous is finished
                searchView.initializeComponents()
            }

            offset = $(window).height() - $('.search-container').offset().top - 30;
            $('.search-scroll-cont').css('height', offset.toString() + 'px');
            scrollContPos = $('.search-container').offset().left -5;

            // Set title left
            $('#search-title').css('left', scrollContPos.toString() + 'px');
        }
            
        if ($('#container-rated-newest').length > 0) {
            // Fixed position in: Homepage in the store view
            var offsetStore;
            var storeWidth;

            offsetStore = $(window).height() - $('#container-rated-newest').offset().top - 30;
            storeWidth = $(window).width() - $('#container-rated-newest').offset().left;
            $('#container-rated-newest').css('height', offsetStore.toString() + 'px');
            $('#container-rated-newest').css('width', storeWidth.toString() + 'px');
        }
    }

    $(window).resize(calculatePositions);
})();
