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
        $('#loading').removeClass('hide');  // Loading view when waiting for requests
        $('#loading').css('height', $(window).height() + 'px');
         $.ajax({
            type: "GET",
            url: endpoint,
            dataType: 'json',
            success: function(response) {
                $('#loading').addClass('hide');
                if (callback) {
                    callback(response);
                } else {
                    paintOfferings(response, container, true);
                }
            },
            error: function(xhr) {
                $('#loading').addClass('hide');
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
                            if (pricePlan.currency == 'EUR') {
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
            mpainter.setState('');
        }

        if (toEmpty) {
            container.empty();
        }

        if (backAct) {
            action = function() {
                backAct();
                mpainter.increase();
                mpainter.setState('');
            }
        }

        for (var i = 0; i < data.length; i++) {
            paintMenuOffering(new OfferingElement(data[i]), container, action, '#home-container');
        }
        if (!evntAllowed) {
            evntAllowed = true;
        }
    }

    setServiceHandler = function setServiceHandler() {
        if ($('.detailed-info').length) {
            $('#home-container').empty()
        }
        searchView.setTitle('Services');
        searchView.initSearchView('SEARCH_TAG_ENTRY', 'service');
    };

    setDataHandler = function setDataHandler() {
        if ($('.detailed-info').length) {
            $('#home-container').empty()
        }
        searchView.setTitle('Data');
        searchView.initSearchView('SEARCH_TAG_ENTRY', 'dataset');
    };

    setWidgetHandler = function setWidgetHandler() {
        if ($('.detailed-info').length) {
            $('#home-container').empty()
        }
        searchView.setTitle('Widgets / Mashups');
        searchView.initSearchView('SEARCH_TAG_ENTRY', 'widget');
    };

    var setContext = function setContext() {
     // Change browser URL
        history.pushState({}, 'FI-WARE Store', '/');
        pageLoader.setCurrentPage('home');
    };

    setSearchListeners = function setSearchListeners(searchV) {
     // Set search listeners
        $('#search').off();
        $('#search').click((function(self) {
            return function() {
                if ($.trim($('#text-search').val()) != '') {
                    self.setTitle('Offerings');
                    self.initSearchView('SEARCH_ENTRY');
                    mpainter.setState('');
                }
            }
        })(searchV));
        // Set listener for enter key
        $('#text-search').off();
        $('#text-search').keypress((function(self) {
            return function(e) {
                if (e.which == 13 && $.trim($(this).val()) != '') {
                    e.preventDefault();
                    e.stopPropagation();
                    self.setTitle('Offerings');
                    self.initSearchView('SEARCH_ENTRY');
                    mpainter.setState('');
                }
            }
        })(searchV));

        $('#all').off();
        $('#all').click((function(self) {
            return function() {
                self.setTitle('Offerings');
                self.initSearchView('OFFERING_COLLECTION');
                mpainter.setState('');
            }
        })(searchV));
    };

    paintHomePage = function paintHomePage () {
        setContext();

        // Create search view object
        searchView = new StoreSearchView();

        $('#home-container').empty();
        $.template('homePageTemplate', $('#home_page_template'));
        $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

        $('#sorting').addClass('hide');
        // Bind menu handlers
        if (!mpainter)  {
            mpainter = new MenuPainter(setServiceHandler, setDataHandler, setWidgetHandler);
        } else {
            mpainter.setState('');
        }

        setSearchListeners(searchView);

        // Get initial offerings
        calculatePositions();
        getOfferings(EndpointManager.getEndpoint('NEWEST_COLLECTION'), $('#newest-container'));
        getOfferings(EndpointManager.getEndpoint('TOPRATED_COLLECTION'), $('#top-rated-container'));
    };

    closeMenuPainter = function closeMenuPainter() {
        mpainter.decrease();
    };

    openMenuPainter = function openMenuPainter() {
        mpainter.increase();
    };

    resetMenuState = function resetMenuState() {
        mpainter.setState('');
    };

    setMenuPainter = function setMenuPainter(menuPainter) {
        mpainter = menuPainter;
    };

    setSearchView = function setSearchView(searchV) {
        searchView = searchV;
    }

    calculatePositions = function calculatePositions(evnt) {
        var position;
        var filabInt = $('#oil-nav').length > 0;

        $('.search-fixed').removeClass('search-fixed');

        if ($('.search-container').length > 0) {
            var offset, scrollContPos;
            // Set class for fixing positions if needed
            if ($(window).width() < 981) {
                $('#store-container').addClass('search-fixed');
            }
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
