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
     * Subclass of StoreSearchView use for kayword based searches
     */
    KeywordSearchView = function KeywordSearchView() {
        this.searchParams = {
            'searching': false,
            'keyword': ''
        };
    };

    KeywordSearchView.prototype = new StoreSearchView();
    KeywordSearchView.prototype.contructor = KeywordSearchView;

    /**
     * Abstract method to be implemented, call the count offerings endpoint
     */
    KeywordSearchView.prototype.countOfferings = function countOfferings(endpoint) {
        getOfferings(endpoint, '', (function(self) {
            return function(offerings) {
                paintOfferings(offerings, $('.search-container'), function() {
                    this.initSearchView('OFFERING_COLLECTION');
                }.bind(this));
            }.bind(self)
        })(this));
    };

    /**
     * Builds the endpoint to be used in the search
     */
    KeywordSearchView.prototype.buildEndpoint = function buildEndpoint(nextPage) {
        // Set pagination params
        var offeringsPage = $('#number-offerings').val();
        var filter = '?start=' + ((offeringsPage * (nextPage - 1)) + 1);
        filter = filter + '&limit=' + offeringsPage;

        // Set sorting params
        if ($('#sorting').val() != '') {
            filter += '&sort=' + $('#sorting').val();
        }

        if (this.searchParams.searching) {
            endpoint = EndpointManager.getEndpoint('SEARCH_ENTRY', {'text': this.searchParams.keyword});
        } else {
            endpoint = EndpointManager.getEndpoint('OFFERING_COLLECTION');
        }

        endpoint = endpoint + filter;
        return endpoint;
    };

    /**
     * Initialize the keyword based search view
     * @param endpoint, Endpoint of the search
     */
    KeywordSearchView.prototype.initSearchView = function initSearchView(endpoint) {
        var endP

        // Paint the search view
        this.paintSearchView();

        if (endpoint == 'SEARCH_ENTRY') {
            this.searchParams.searching = true;
            this.searchParams.keyword = $.trim($('#text-search').val());
            endP = EndpointManager.getEndpoint(endpoint, {'text': $.trim($('#text-search').val())}) + '?action=count';
        } else {
            this.searchParams.searching = false;
            this.searchParams.keyword = '';
            endP = EndpointManager.getEndpoint(endpoint) + '?action=count';
        }

        // Set listener for number of offerings select
        $('#number-offerings').change((function(self, endPoint) {
            return function() {
                getOfferings(endP, '', function(offerings) {
                    self.setPaginationParams(offerings);
                });
            };
        })(this, endP));

        // Set listener for sorting select
        $('#sorting').change((function(self, endPoint) {
            return function() {
                getOfferings(endP, '', function(offerings) {
                    self.setPaginationParams(offerings);
                });
            };
        })(this, endP));

        // Calculate the number of offerings
        getOfferings(endP, '', function(offerings) {
            this.setPaginationParams(offerings);
        }.bind(this));
    };
})();