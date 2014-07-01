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

    CatalogueSearchView = function CatalogueSearchView() {
        this.searchParams = {
            'keyword': '',
            'searching': false
        };
        this.query = '';
    };

    CatalogueSearchView.prototype.scrollHandler = function scrollHandler() {
        
    };

    CatalogueSearchView.prototype.painterHandler = function painterHandler(offerings) {
        var toEmpty = false;

        if (this.pagination.getNextPageNumber() <= 2) { // Is the first page
            if (offerings.length > 0) {
                toEmpty = true;  // Delete the container
            } else {
                var msg = 'Your search has not produced any results'; 
                if (!this.searchParams.searching) {
                    msg = "Your don't have any offering in this category";
                }
                MessageManager.showAlertInfo('No offerings', msg, $('.offerings-container'));
                $('.offerings-container .alert-info').removeClass('span8');
                return;
            }
        }
        paintProvidedOfferings(offerings, toEmpty);
    };

    var paintProvidedOfferings = function paintProvidedOfferings (data, toEmpty) {

        action = function() {
            paintCatalogue();
            getMenuPainter().increase();
        };

        if (toEmpty) {
            $('.offerings-container').empty();
        }
        for (var i = 0; i < data.length; i++) {
            var offering_elem = new OfferingElement(data[i]);
            var offDetailsView = new CatalogueDetailsView(offering_elem, action, '#catalogue-container');
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

            priceStr = getPriceStr(offering_elem.getPricing());
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
            templ.appendTo('.offerings-container');
        }
        notifyEvent();
    };

    CatalogueSearchView.prototype.initializeComponents = function initializeComponents(type) {
        var offset, nrows;

        if (type) {
            if (type == 'provided') {
                this.query = '&filter=provided&state=all';
                $('#catalogue-title').text('Provided');
            } else {
                this.query = '&filter=purchased';
                $('#catalogue-title').text('Purchased');
            }
        }

        $('.offerings-container').empty();
        // Calculate the number of rows
        offset = $('.offerings-scroll-container').offset().top;
        nrows = Math.floor((($(window).height() - offset)/167) + 1);

        // Set listener for sorting select
        $('#sorting').change((function(self, endPoint) {
            return function() {
                var query = self.query;
                if ($('#sorting').val() != '') {
                    query += '&sort=' + $('#sorting').val();
                }
                $('.offerings-container').empty();
                self.pagination.removeListeners();
                self.pagination.createListeners();
                self.pagination.configurePaginationParams(320, nrows, query);
                self.pagination.getNextPage();
            };
        })(this, this.calculatedEndp));

        this.pagination.setElemSpace(0);
        this.pagination.configurePaginationParams(320, nrows, this.query);

        // Remove possible listeners existing in the scroll
        this.pagination.removeListeners();

        this.pagination.createListeners();
        this.pagination.getNextPage();
    };

    CatalogueSearchView.prototype.initSearchView = function initSearchView(endpoint, type) {
        this.searchEndp = endpoint;

        // Check if an specific search endpoint has been provided
        if (endpoint != 'OFFERING_COLLECTION') {
            this.searchParams.searching = true;
            // Check if a search word has been provided or if it is needed
            // to retrieve it from the form field
            this.searchParams.keyword = $.trim($('#cat-search-input').val());
            this.calculatedEndp = EndpointManager.getEndpoint(endpoint, {'text': this.searchParams.keyword});
        } else {
            // Get all offerings
            this.searchParams.searching = false;
            this.searchParams.keyword = '';
            this.calculatedEndp = EndpointManager.getEndpoint(endpoint);
        }

        // Create the client
        this.client = new ServerClient('', this.calculatedEndp, true);
        // Create pagination component
        this.pagination = new ScrollPagination(
            $('.offerings-scroll-container'),
            $(".offerings-container"),
            this.painterHandler.bind(this),
            this.client,
            this.scrollHandler.bind(this)
        );

        this.initializeComponents(type);
    };

})();
