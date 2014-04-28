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
        this.numberOfPages = 1;
        this.currentPage = 1;
    }

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
            this.countOfferings(endpoint);
        }
    };

    /**
     * Abstract method to be implemented, call the count offerings endpoint
     */
    StoreSearchView.prototype.countOfferings = function countOfferings(endpoint) {
    };

    /**
     * Abstract method to be implemented, builds the endpoint 
     */
    StoreSearchView.prototype.buildEndpoint = function buildEndpoint() {
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
                        self.initSearchView('SEARCH_ENTRY');
                    }
                }
            })(this));
            // Set listener for enter key
            $('#text-search').keypress((function(self) {
                return function(e) {
                    if (e.which == 13 && $.trim($(this).val()) != '') {
                        e.preventDefault();
                        e.stopPropagation();
                        self.initSearchView('SEARCH_ENTRY');
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

        ret = $('<a></a>').text('Return').attr('id', 'store-return').appendTo('#store-container');
        ret.click(paintHomePage);

        $.template('storeSearchTemplate', $('#store_search_template'));
        $.tmpl('storeSearchTemplate').appendTo('#store-container');
        calculatePositions();
    };

    /**
     * Abstract method that initialize the search view
     */
    StoreSearchView.prototype.initSearchView = function initSearchView(endpoint) {
    };
})();