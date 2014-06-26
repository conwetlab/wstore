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
            'keyword': ''
        };
    }

    /**
     * Set the endpoint to be used in searches
     * @param endpoint, Search endpoint to be used
     */
    StoreSearchView.prototype.setSearchEndpoint = function setSearchEndpoint(endpoint) {
        this.searchEndp = endpoint;
    };

    StoreSearchView.prototype.scrollHandler = function scrollHandler(evnt) {
        
    };

    StoreSearchView.prototype.painterHandler = function painterHandler(offerings) {
        paintOfferings(offerings, $('.search-container'), false, function() {
            this.initSearchView('OFFERING_COLLECTION');
        }.bind(this));
    };

    StoreSearchView.prototype.paintSearchView = function paintSearchView() {
        var ret, title='Offerings';

        // Check if the main page template has been destroyed and 
        // create it again if needed
        if ($('#store-search').length == 0) {
            $.template('homePageTemplate', $('#home_page_template'));
            $.tmpl('homePageTemplate',  {}).appendTo('#home-container');

            // Set search listeners
            $('#search').click((function(self) {
                return function() {
                    if ($.trim($('#text-search').val()) != '') {
                        self.initSearchView(this.searchEndp);
                    }
                }
            })(this));
            // Set listener for enter key
            $('#text-search').keypress((function(self) {
                return function(e) {
                    if (e.which == 13 && $.trim($(this).val()) != '') {
                        e.preventDefault();
                        e.stopPropagation();
                        self.initSearchView(this.searchEndp);
                    }
                }
            })(this));

            $('#all').click((function(self) {
                return function() {
                    self.initSearchView('OFFERING_COLLECTION');
                }
            })(this))
        }

        $('#store-container').empty()

        if (this.searchEndp == 'SEARCH_TAG_ENTRY') {
            title = this.searchParams.keyword;
        }
        $.template('storeSearchTemplate', $('#store_search_template'));
        $.tmpl('storeSearchTemplate', {'title': title}).appendTo('#store-container');
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
            } else {
                this.searchParams.keyword = searchWord;
            }
            this.calculatedEndp = EndpointManager.getEndpoint(endpoint, {'text': this.searchParams.keyword});
        } else {
            // Get all offerings
            this.searchParams.searching = false;
            this.searchParams.keyword = '';
            this.calculatedEndp = EndpointManager.getEndpoint(endpoint);
        }
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