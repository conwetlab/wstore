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
    StoreSearchView = function StoreSearchView(searchEndp) {
        this.numberOfPages = 1;
        this.currentPage = 1;
        this.searchParams = {
            'searching': false,
            'keyword': ''
        };
        this.searchEndp = searchEndp;
    }

    /**
     * Set the endpoint to be used in searches
     * @param endpoint, Search endpoint to be used
     */
    StoreSearchView.prototype.setSearchEndpoint = function setSearchEndpoint(endpoint) {
        this.searchEndp = endpoint;
    };

    /**
     * Set the needed params to support pagination
     * @param numberOfOfferings, Number of offerings expected to be returned
     */
    StoreSearchView.prototype.setPaginationParams = function setPaginationParams(numberOfOfferings) {
        // Calculate the number of pages
        this.numberOfPages = Math.ceil(numberOfOfferings.number / $('#number-offerings').val());
        this.refreshPagination(1);
        this.getNextOfferings(1);
    };

    /**
     * Get the next offerings according to the next page
     * @param nextPage, Next page to be shown
     */
    StoreSearchView.prototype.getNextOfferings = function getNextOfferings(nextPage) {
        // Show a message if there are no results
        if (this.numberOfPages == 0) {
            var msg = 'Your search has not produced any results';
            this.refreshPagination(nextPage);

            MessageManager.showAlertInfo('No offerings', msg, $('.search-container'))

        } else {
            // Build endpoint
            var endpoint = this.buildEndpoint(nextPage);

            this.refreshPagination(nextPage);
            getOfferings(endpoint, '', (function(self) {
                return function(offerings) {
                    paintOfferings(offerings, $('.search-container'), function() {
                        this.initSearchView('OFFERING_COLLECTION');
                    }.bind(this));
                }.bind(self)
            })(this));
        }
    };

    /**
     * Abstract method to be implemented, builds the endpoint 
     */
    StoreSearchView.prototype.buildEndpoint = function buildEndpoint(nextPage) {
     // Set pagination params
        var offeringsPage = $('#number-offerings').val();
        var filter = '?start=' + ((offeringsPage * (nextPage - 1)) + 1);
        filter = filter + '&limit=' + offeringsPage;

        // Set sorting params
        if ($('#sorting').val() != '') {
            filter += '&sort=' + $('#sorting').val();
        }

        if (this.searchParams.searching) {
            endpoint = EndpointManager.getEndpoint(this.searchEndp, {'text': this.searchParams.keyword});
        } else {
            endpoint = EndpointManager.getEndpoint('OFFERING_COLLECTION');
        }

        endpoint = endpoint + filter;
        return endpoint;
    };

    /**
     * Refresh the pagination component according to the next page to
     * be displayed
     * @param self, Object reference
     * @param nextPage, Next page to be displayed 
     */
    StoreSearchView.prototype.refreshPagination = function refreshPagination (nextPage) {
        var numberElem = 3;
        var activatedPosition = 1;
        var pagElems, button, a, currElem;

        // calculate the number of displayed elements
        if (this.numberOfPages < 3) {
            numberElem = this.numberOfPages;
        }

        // Calculate activated position
        if (this.numberOfPages >= 3) {
            if (nextPage == this.numberOfPages) {
                activatedPosition = 3;
                finalSecuence = true;
            } else if (nextPage == (this.numberOfPages - 1)) {
                activatedPosition = 2;
            }
        } else {
            activatedPosition = nextPage;
        }

        // paint the new pagination element
        $('.pagination').empty();
        pagElems = $('<ul></ul>');

        button = $('<li></li>').attr('id', 'prev');
        a = $('<a></a>').append('<i></i>').attr('class', 'icon-chevron-left');
        a.appendTo(button);

        // Set prev button listener
        if(nextPage != 1) {
            button.click((function (self, page) {
                return function () {
                    self.getNextOfferings(page - 1);
                };
            })(this, nextPage));
        }

        button.appendTo(pagElems);

        if (activatedPosition == 1) {
            currElem = nextPage;
        } else if (activatedPosition == 2) {
            currElem = nextPage - 1;
        } else if (activatedPosition == 3) {
            currElem = nextPage - 2;
        }

        for(var i = 0; i < numberElem; i++) {
            button = $('<li></li>');
            a = $('<a></a>').text(currElem);
            if (currElem == nextPage) {
                button.attr('class', 'active');
            }
            a.appendTo(button);

            // Set the numbered button listener
            button.click((function (self, page) {
                return function () {
                    self.getNextOfferings(page);
                };
            })(this, currElem));

            button.appendTo(pagElems);
            currElem ++;
        }

        button = $('<li></li>').attr('id', 'next');
        a = $('<a></a>').append('<i></i>').attr('class', 'icon-chevron-right');
        a.appendTo(button);

        // Set prev button listener
        if(nextPage != this.numberOfPages) {
            button.click((function (self, page) {
                return function () {
                    self.getNextOfferings(page + 1);
                }
            })(this, nextPage));
        }

        button.appendTo(pagElems);

        pagElems.appendTo('.pagination');
    };

    StoreSearchView.prototype.paintSearchView = function paintSearchView() {
        var ret;

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

        $.template('storeSearchTemplate', $('#store_search_template'));
        $.tmpl('storeSearchTemplate').appendTo('#store-container');
        ret = $('#store-return');
        ret.click(paintHomePage);

        calculatePositions();
    };

    /**
     * Abstract method that initialize the search view
     */
    StoreSearchView.prototype.initSearchView = function initSearchView(endpoint, searchWord) {
        var endP;

        // Paint the search view
        this.paintSearchView();

        // Check if an specific search endpoint has been provided
        if (endpoint == this.searchEndp) {
            this.searchParams.searching = true;
            // Check if a search word has been provided or if it is needed
            // to retrieve it from the form field
            if (!searchWord) {
                this.searchParams.keyword = $.trim($('#text-search').val());
            } else {
                this.searchParams.keyword = searchWord;
            }
            endP = EndpointManager.getEndpoint(endpoint, {'text': this.searchParams.keyword}) + '?action=count';
        } else {
            // Get all offerings
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