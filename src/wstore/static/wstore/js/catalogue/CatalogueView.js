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

    var mpainter;
    var searchView;
    var evntAllowed = true;
    var currentView = 'purchased';

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

    var getRepositories = function getRepositories(callback) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('REPOSITORY_COLLECTION'),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var purchasedHandler = function purchasedHandler() {
            // Check if details view
            if ($('.detailed-info').length) {
                $('#catalogue-container').empty();
                createCatalogueContents();
            }
            currentView = 'purchased';
            searchView.initSearchView('OFFERING_COLLECTION', 'purchased');
    }

    var providedHandler = function providedHandler() {
     // Check if details view
        if ($('.detailed-info').length) {
            $('#catalogue-container').empty();
            createCatalogueContents();
        }

        currentView = 'provided';

        if (USERPROFILE.getCurrentRoles().indexOf('provider') != -1) {
            searchView.initSearchView('OFFERING_COLLECTION', 'provided');
        } else {
            // Build the non-provider view
            var msg;
            if (USERPROFILE.getCurrentOrganization() == USERPROFILE.getUsername()) {
                msg = "You don't have the provider role. To request the role please click ";
                if (USERPROFILE.providerRequested()) {
                    msg = "You don't have the provider role yet. Your request is pending for approval";
                }
            } else {
                msg = "You don't have the provider role for the current organization. Ask an organization manager to request the role";
            }
            $('#catalogue-title').text('Provided');
            MessageManager.showAlertInfo('Unauthorized', msg, $('.offerings-container'));
            $('.offerings-container .alert-info').removeClass('span8');

            if ((USERPROFILE.getCurrentOrganization() == USERPROFILE.getUsername()) && !USERPROFILE.providerRequested()) {
                var reqBtn = $('<a>here</a>');
                var requestForm = new ProviderRequestForm(USERPROFILE);

                reqBtn.click(function() {
                    requestForm.display();
                }).appendTo('.alert-info');
            }
        }
    };

    closeMenuPainter = function closeMenuPainter() {
        mpainter.decrease();
    };

    createCatalogueContents = function createCatalogueContents() {
     // Get the catalogue template
        $.template('catalogueTemplate', $('#catalogue_search_template'));
        $.tmpl('catalogueTemplate', {}).appendTo('#catalogue-container');

        // If the user is a provider, append provider buttons
        if (USERPROFILE.getCurrentRoles().indexOf('provider') != -1) {
            $.template('providerOptionsTemplate', $('#provider_options_template'));
            $.tmpl('providerOptionsTemplate', {}).appendTo('#provider-options');

            $('#create-app').click(function () {
                getRepositories(showCreateAppForm);
            });
            $('#register-res').click(function() {
                var regResForm = buildRegisterResourceForm('create');
                regResForm.display();
            });
            $('#view-res').click(function() {
                var resForm, offElem = {}
                offElem.getResources = function() {
                    return [];
                }
                resForm = new BindResourcesForm(offElem, true);
                resForm.display();
            });

        }
        $('#cat-search').click(function() {
            var keyword = $.trim($('#cat-search-input').val());
            if (keyword != ''){
                searchView.initSearchView('SEARCH_ENTRY');
            }
        });

        // Set listener for enter key
        $('#cat-search-input').keypress(function(e) {
            var keyword = $.trim($('#cat-search-input').val());

            if (e.which == 13 && keyword != '') {
                e.preventDefault();
                e.stopPropagation();
                searchView.initSearchView('SEARCH_ENTRY');
            }
        });
        $('#cat-all').click(function() {
            searchView.initSearchView('OFFERING_COLLECTION');
        });
        calculatePositions();
    };

    paintCatalogue = function paintCatalogue(useContents) {

        history.pushState({}, 'FI-WARE Store', '/catalogue');

        if (!useContents) {
            createCatalogueContents();
        }
        searchView = new CatalogueSearchView();

        // Create menu
        if (!mpainter) {
            mpainter = new MenuPainter(purchasedHandler, providedHandler);
        }

        searchView.initSearchView('OFFERING_COLLECTION', currentView);
    };


    getMenuPainter = function getMenuPainter() {
        return mpainter;
    };

    setView = function setView(view) {
        currentView = view;
    };

    getCurrentView = function getCurrentView() {
        return currentView;
    }

    notifyEvent = function notifyEvent() {
        evntAllowed = true;
    };

    calculatePositions = function calculatePositions(evnt) {

        if ($('.offerings-scroll-container').length) {
            if (evnt && evntAllowed) {
                evntAllowed = false;
                searchView.initializeComponents();
            }

            var scrollContPos, offset = $(window).height() - $('.offerings-scroll-container').offset().top - 30;

            $('.offerings-scroll-container').css('height', offset.toString() + 'px');

            scrollContPos = $('.offerings-container').offset().left -5;
            // Set title left
            $('#catalogue-title').css('left', scrollContPos.toString() + 'px');

        }
    }

    $(window).resize(calculatePositions);

})();
