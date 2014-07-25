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

    /**
     * View where offering search results are shown
     */
    StoreSearchView = function StoreSearchView() {
        this.searchParams = {
            'searching': false,
            'keyword': '',
            'params': {}
        };
        this.title = 'Offerings';
        this.allowedEndpoints = {
            'OFFERING_COLLECTION': {
                'page': 'offerings',
                'data': function(){}
            },
            'SEARCH_ENTRY': {
                'page': 'keyword',
                'data': this.getKeyword.bind(this)
            },
            'SEARCH_TAG_ENTRY': {
                'page': 'tag',
                'data': this.getKeyword.bind(this)
            },
            'SEARCH_RESOURCE_ENTRY': {
                'page': 'resource',
                'data': this.getParams.bind(this)
            }
        }
    }

    StoreSearchView.prototype.getKeyword = function getKeyword() {
        return this.searchParams.keyword;
    };

    StoreSearchView.prototype.getParams = function getParams() {
        return this.searchParams.params;
    };

    /**
     * Set the endpoint to be used in searches
     * @param endpoint, Search endpoint to be used
     */
    StoreSearchView.prototype.setSearchEndpoint = function setSearchEndpoint(endpoint) {
        this.searchEndp = endpoint;
    };

    StoreSearchView.prototype.setTitle = function setTitle(title) {
        this.title = title;
    };

    StoreSearchView.prototype.scrollHandler = function scrollHandler(evnt) {
        
    };

    StoreSearchView.prototype.painterHandler = function painterHandler(offerings) {
        var toEmpty = false;

        if (this.pagination.getNextPageNumber() <= 2) { // Is the first page
            if (offerings.length > 0) {
                toEmpty = true;  // Delete the container
            } else {
                var msg = 'Your search has not produced any results';
                MessageManager.showAlertInfo('No offerings', msg, $('.search-container'));
                $('.search-container .alert-info').removeClass('span8');
                return;
            }
        }
        paintOfferings(offerings, $('.search-container'), toEmpty, function() {
            this.setTitle('Offerings');
            this.initSearchView('OFFERING_COLLECTION');
        }.bind(this));
    };

    StoreSearchView.prototype.paintSearchView = function paintSearchView() {
        var ret;

        // Check if the main page template has been destroyed and 
        // create it again if needed

        if (!$('#store-container').length) {
            $('<div class="clear space" /><div class="row-fluid" id="store-container"></div>').appendTo('#home-container');
        }

        setSearchListeners(this);

        $('#store-container').empty()

        $.template('storeSearchTemplate', $('#store_search_template'));
        $.tmpl('storeSearchTemplate', {'title': this.title}).appendTo('#store-container');
        ret = $('#store-return');
        ret.click(paintHomePage);

        calculatePositions();
    };

    /**
     * Initialize listeners and pagination
     */
    StoreSearchView.prototype.initializeComponents = function initializeComponents() {
        var offset, nrows;

        $('.search-container').empty();
        // Calculate the number of rows
        offset = $('.search-scroll-cont').offset().top;
        nrows = Math.floor((($(window).height() - offset)/167) + 1);

        // Set listener for sorting select
        $('#sorting').change((function(self, endPoint) {
            return function() {
                var query = '';
                if ($('#sorting').val() != '') {
                    query = '&sort=' + $('#sorting').val();
                }
                $('.search-container').empty();
                self.pagination.removeListeners();
                self.pagination.createListeners();
                self.pagination.configurePaginationParams(320, nrows, query);
                self.pagination.getNextPage();
            };
        })(this, this.calculatedEndp));

        this.pagination.setElemSpace(0);
        this.pagination.configurePaginationParams(320, nrows);

        // Remove possible listeners existing in the scroll
        this.pagination.removeListeners();

        this.pagination.createListeners();
        this.pagination.getNextPage();
    };

    StoreSearchView.prototype.setBrowserState = function setBrowserState() {
        var clientURL;

        if (this.searchEndp != 'OFFERING_COLLECTION' && this.searchEndp != 'SEARCH_RESOURCE_ENTRY') {
            clientURL = EndpointManager.getClientEndpoint(this.searchEndp, {'text': this.searchParams.keyword});
        } else if (this.searchEndp == 'SEARCH_RESOURCE_ENTRY'){
            clientURL = EndpointManager.getClientEndpoint(this.searchEndp, this.searchParams.params);
        } else {
            clientURL = EndpointManager.getClientEndpoint(this.searchEndp);
        }
        history.pushState({}, 'FI-WARE Store', clientURL);
        pageLoader.setCurrentPage(this.allowedEndpoints[this.searchEndp].page);
        INIT_INFO = this.allowedEndpoints[this.searchEndp].data()
    };
    /**
     * Initialize the search view
     */
    StoreSearchView.prototype.initSearchView = function initSearchView(endpoint, searchWord) {

        this.searchEndp = endpoint;

        // Check if an specific search endpoint has been provided
        if (endpoint != 'OFFERING_COLLECTION') {
            this.searchParams.searching = true;
            // Check if a search word has been provided or if it is needed
            // to retrieve it from the form field
            if (!searchWord) {
                this.searchParams.keyword = $.trim($('#text-search').val());
                this.calculatedEndp = EndpointManager.getEndpoint(endpoint, {'text': this.searchParams.keyword});
            } else if (typeof searchWord == 'string' || searchWord instanceof String){
                this.searchParams.keyword = searchWord;
                this.calculatedEndp = EndpointManager.getEndpoint(endpoint, {'text': this.searchParams.keyword});
            } else {
                this.searchParams.params = searchWord;
                this.calculatedEndp = EndpointManager.getEndpoint(endpoint, searchWord);
            }
        } else {
            // Get all offerings
            this.searchParams.searching = false;
            this.searchParams.keyword = '';
            this.calculatedEndp = EndpointManager.getEndpoint(endpoint);
        }

        this.setBrowserState();

        // Paint the search view
        this.paintSearchView();

        // Create the client
        this.client = new ServerClient('', this.calculatedEndp, true);
        // Create pagination component
        this.pagination = new ScrollPagination(
            $('.search-scroll-cont'),
            $(".search-container"),
            this.painterHandler.bind(this),
            this.client,
            this.scrollHandler.bind(this)
        );

        this.initializeComponents();
    };
})();