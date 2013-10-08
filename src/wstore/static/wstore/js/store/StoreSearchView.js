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

    var numberOfPages = 1;
    var currentPage = 1;
    var searchParams = {
        'searching': false,
        'keyword': ''
    };

    var setPaginationParams = function setPaginationParams(numberOfOfferings) {
        numberOfPages = Math.ceil(numberOfOfferings.number / $('#number-offerings').val());
        refreshPagination(1);
        getNextOfferings(1);
    };

    var getNextOfferings = function getNextOfferings(nextPage) {
        if (numberOfPages == 0) {
            var msg = 'Your search has not produce any results';
            refreshPagination(nextPage);

            MessageManager.showAlertInfo('No offerings', msg, $('.search-container'))

        } else {
            var offeringsPage = $('#number-offerings').val();

            // Set pagination params
            var filter = '?start=' + ((offeringsPage * (nextPage - 1)) + 1);
            filter = filter + '&limit=' + offeringsPage;

            // Set sorting params
            if ($('#sorting').val() != '') {
                filter += '&sort=' + $('#sorting').val();
            }

            if (searchParams.searching) {
                endpoint = EndpointManager.getEndpoint('SEARCH_ENTRY', {'text': searchParams.keyword});
            } else {
                endpoint = EndpointManager.getEndpoint('OFFERING_COLLECTION');
            }

            endpoint = endpoint + filter;

            refreshPagination(nextPage);
            getOfferings(endpoint, '', function(offerings) {
                paintOfferings(offerings, $('.search-container'), function() {
                    initSearchView('OFFERING_COLLECTION');
                });
            });
        }
    };

    var refreshPagination = function refreshPagination (nextPage) {
        var numberElem = 3;
        var activatedPosition = 1;
        var pagElems, button, a, currElem;

        // calculate the number of displayed elements
        if (numberOfPages < 3) {
            numberElem = numberOfPages;
        }

        // Calculate activated position
        if (numberOfPages >= 3) {
            if (nextPage == numberOfPages) {
                activatedPosition = 3;
                finalSecuence = true;
            } else if (nextPage == (numberOfPages - 1)) {
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
            button.click((function (page) {
                return function () {
                    getNextOfferings(page - 1);
                };
            })(nextPage));
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
            button.click((function (page) {
                return function () {
                    getNextOfferings(page);
                };
            })(currElem));

            button.appendTo(pagElems);
            currElem ++;
        }

        button = $('<li></li>').attr('id', 'next');
        a = $('<a></a>').append('<i></i>').attr('class', 'icon-chevron-right');
        a.appendTo(button);

        // Set prev button listener
        if(nextPage != numberOfPages) {
            button.click((function (page) {
                return function () {
                    getNextOfferings(page + 1);
                }
            })(nextPage));
        }

        button.appendTo(pagElems);

        pagElems.appendTo('.pagination');
    };

    var paintSearchView = function paintSearchView() {
        var ret;

        // Check if the main page template has been destroyed and 
        // create it again if needed
        if ($('#store-search').length == 0) {
            $.template('homePageTemplate', $('#home_page_template'));
            $.tmpl('homePageTemplate',  {}).appendTo('#home-container');
            // Set search listeners
            $('#search').click(function() {
                if ($.trim($('#text-search').val()) != '') {
                    initSearchView('SEARCH_ENTRY');
                }
            });
            // Set listener for enter key
            $('#text-search').keypress(function(e) {
                if (e.which == 13 && $.trim($(this).val()) != '') {
                    e.preventDefault();
                    e.stopPropagation();
                    initSearchView('SEARCH_ENTRY');
                }
            });
            $('#all').click(function() {
                initSearchView('OFFERING_COLLECTION');
            })
        }

        $('#store-container').empty()

        ret = $('<a></a>').text('Return').attr('id', 'store-return').appendTo('#store-container');
        ret.click(paintHomePage);

        $.template('storeSearchTemplate', $('#store_search_template'));
        $.tmpl('storeSearchTemplate').appendTo('#store-container');
        calculatePositions();
    };

    initSearchView = function initSearchView(endpoint) {
        var endP

        // Paint the search view
        paintSearchView();

        if (endpoint == 'SEARCH_ENTRY') {
            searchParams.searching = true;
            searchParams.keyword = $.trim($('#text-search').val());
            endP = EndpointManager.getEndpoint(endpoint, {'text': $.trim($('#text-search').val())}) + '?action=count';
        } else {
            searchParams.searching = false;
            searchParams.keyword = '';
            endP = EndpointManager.getEndpoint(endpoint) + '?action=count';
        }

        // Set listener for number of offerings select
        $('#number-offerings').change((function(endPoint) {
            return function() {
                getOfferings(endP, '', setPaginationParams);
            };
        })(endP));

        // Set listener for sorting select
        $('#sorting').change((function(endPoint) {
            return function() {
                getOfferings(endP, '', setPaginationParams);
            };
        })(endP));

        // Calculate the number of offerings
        getOfferings(endP, '', setPaginationParams);
    };
})();