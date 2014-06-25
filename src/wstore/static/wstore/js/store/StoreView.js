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

    paintOfferings = function paintOfferings(data, container, backAct) {
        var action = paintHomePage;
        container.empty();

        if (backAct) {
            action=backAct;
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
    }

    paintHomePage = function paintHomePage () {
        // Create search view object
        var searchView = new StoreSearchView('SEARCH_ENTRY');
        var mpainter;

        $('#home-container').empty();
        $.template('homePageTemplate', $('#home_page_template'));
        $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

        $('#search').click(function() {
            if ($.trim($('#text-search').val()) != '') {
                searchView.initSearchView('SEARCH_ENTRY');
            }
        });

        // Set listener for enter key
        $('#text-search').keypress(function(e) {
            if (e.which == 13 && $.trim($(this).val()) != '') {
                e.preventDefault();
                e.stopPropagation();
                searchView.initSearchView('SEARCH_ENTRY');
            }
        });

        $('#all').click(function() {
            searchView.initSearchView('OFFERING_COLLECTION');
        })

        if (USERPROFILE.getUserRoles().indexOf('admin') == -1 && $('#oil-nav').length > 0) {
            // The navigation menu width depends on the presence of the FI-LAB bar
            $('.navigation').css('width', '188px');
        }
        // Bind menu handlers
        mpainter = new MenuPainter();
        // Get initial offerings
        calculatePositions();
        getOfferings(EndpointManager.getEndpoint('NEWEST_COLLECTION'), $('#newest-container'));
        getOfferings(EndpointManager.getEndpoint('TOPRATED_COLLECTION'), $('#top-rated-container'));
    };

    calculatePositions = function calculatePositions() {
        var position;
        var filabInt = $('#oil-nav').length > 0;

        // Check window width
        if ($(window).width() < 981) {

            // Check if search view is active
            if ($('.search-container').length > 0) {
                $('.catalogue-form .form').removeAttr('style');
                $('.catalogue-form').css('margin-left', '0');
                if ($(window).width() < 769) { // Responsive activation width
                    var sortMargin;

                    $('.catalogue-form .form').css('width', '100%');
                    $('.pagination').removeAttr('style');
                    $('.search-container').removeAttr('style');
                    $('.search-container').css('left', '20px');

                    if (!filabInt) {
                        $('.search-container').css('top', '427px');
                    }

                    // Calculate sorting position
                    sortMargin = Math.floor(($(window).width()/2) - $('#sorting').width() -12);
                    $('#sorting').css('margin-left', sortMargin + 'px');
                    $('h2:contains(Sort by)').css('margin-left', sortMargin + 'px');
                } else {
                    var offset;
                    var searchWidth;
                    $('.catalogue-form').css('margin-left', '0');
                    $('.search-container').removeAttr('style');

                    if (filabInt) {
                        $('.search-container').css('top', '130px');
                    } else {
                        $('.search-container').css('top', '280px');
                    }

                    $('#sorting').removeAttr('style');
                    $('h2:contains(Sort by)').removeAttr('style');
                    offset = $(window).height() - $('.search-container').offset().top - 30;
                    searchWidth = $(window).width() - $('.search-container').offset().left;
                    $('.search-container').css('height', offset.toString() + 'px');
                    $('.search-container').css('width', searchWidth.toString() + 'px');
                }
            } else if ($('#container-rated-newest').length > 0) {
                // Fixed position in: Homepage in the store view
                var offsetStore;
                var storeWidth;

                offsetStore = $(window).height() - $('#container-rated-newest').offset().top - 30;
                storeWidth = $(window).width() - $('#container-rated-newest').offset().left;
                $('#container-rated-newest').css('height', offsetStore.toString() + 'px');
                $('#container-rated-newest').css('width', storeWidth.toString() + 'px');
            }
        } else {
            if ($('.search-container').length > 0) {
                // Fixed position in: Search options in the store view
                var offset;
                var searchWidth;

                $('.catalogue-form .form').removeAttr('style');
                $('.catalogue-form').css('margin-left', '0');
                $('.search-container').removeAttr('style');
                $('#sorting').removeAttr('style');
                $('h2:contains(Sort by)').removeAttr('style');
                offset = $(window).height() - $('.search-container').offset().top - 30;
                searchWidth = $(window).width() - $('.search-container').offset().left;
                $('.search-container').css('height', offset.toString() + 'px');
                $('.search-container').css('width', searchWidth.toString() + 'px');
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

        // Check username length to avoid display problems
        if ($.trim($('div.btn.btn-blue > div.dropdown-toggle span').text()).length > 12) {
            var shortName = ' '+ USERPROFILE.getCompleteName().substring(0, 9) + '...';
            // Replace user button contents
            var userBtn = $('div.btn.btn-blue > div.dropdown-toggle span');
            userBtn.empty();
            userBtn.text(shortName);
        }
    }

    $(window).resize(calculatePositions);
})();
