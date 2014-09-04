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
                    msg = "You don't have any offering in this category";
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
            paintMenuOffering(new OfferingElement(data[i]), $('.offerings-container'), action, '#catalogue-container');
        }
        notifyEvent();
    };

    var sortingHandler = function sortingHandler(self, value, nrows) {
        var query = self.query;
        if (value != '') {
            query += '&sort=' + value;
        }
        $('.offerings-container').empty();
        self.pagination.removeListeners();
        self.pagination.createListeners();
        self.pagination.configurePaginationParams(320, nrows, query);
        self.pagination.getNextPage();
    };

    CatalogueSearchView.prototype.initializeComponents = function initializeComponents(type) {
        var offset, nrows;

        if (type) {
            if (type == 'provided') {
                this.query = '&filter=provided&state=all';
                $('#catalogue-title').text('Provided');
            } else {
                this.query = '&filter=purchased';
                $('#catalogue-title').text('Acquired');
            }
        }

        $('.offerings-container').empty();
        // Calculate the number of rows
        offset = $('.offerings-scroll-container').offset().top;
        nrows = Math.floor((($(window).height() - offset)/167) + 1);

        // Set listener for sorting
        $('#sort-pop').click(function(self, value) {
            return function() {
                sortingHandler(self, value, nrows);
            };
        }(this, 'popularity'));

        $('#sort-name').click(function(self, value) {
            return function() {
                sortingHandler(self, value, nrows);
            };
        }(this, 'name'));

        $('#sort-date').click(function(self, value) {
            return function() {
                sortingHandler(self, value, nrows);
            };
        }(this, 'date'));

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
