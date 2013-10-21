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

    var currentTab;
    var currentPage = 1;
    var numberOfPages = 1;

    var searchParams = {
        'keyword': '',
        'searching': false
    };

    var getNextUserOfferings = function getNextUserOfferings (nextPage) {
        var endpoint;

        // Set the pagination values in catalogue search view
        setNextPage(nextPage);
        // refresh pagination element
        refreshPagination(nextPage);
        currentPage = nextPage;

        // make get offerings request
        // Calculate the endpoint of the request
        if (searchParams.searching) {
            endpoint = EndpointManager.getEndpoint('SEARCH_ENTRY', {'text': searchParams.keyword});
        } else {
            endpoint = EndpointManager.getEndpoint('OFFERING_COLLECTION')
        }

        getUserOfferings(currentTab, paintProvidedOfferings, endpoint);
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
                    getNextUserOfferings(page - 1);
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
                    getNextUserOfferings(page);
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
                    getNextUserOfferings(page + 1);
                }
            })(nextPage));
        }

        button.appendTo(pagElems);

        pagElems.appendTo('.pagination');
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

    var setPaginationParams = function setPaginationParams (target, count) {
        var numberOfOfferings;

        numberOfOfferings = count.number;

        if (numberOfOfferings != 0) {
            numberOfPages = Math.ceil(numberOfOfferings / $('#number-offerings').val());
        } else {
            numberOfPages = 1;
        }

        getNextUserOfferings(1);
    };

    var changeTab = function changeTab (tab, changeMode) {
        var endpoint;

        currentTab = tab;

        if (changeMode) {
            searchParams.keyword = '';
            searchParams.searching = false;
        }

        if (searchParams.searching) {
            endpoint = EndpointManager.getEndpoint('SEARCH_ENTRY', {'text': searchParams.keyword})
        } else {
            endpoint = EndpointManager.getEndpoint('OFFERING_COLLECTION')
        }
        getUserOfferings(tab, setPaginationParams, endpoint, true);
    };

    paintCatalogue = function paintCatalogue() {
        // Get the catalogue template
        $.template('catalogueTemplate', $('#catalogue_search_template'));
        $.tmpl('catalogueTemplate', {}).appendTo('#catalogue-container');

        // If the user is a provider, append provider buttons
        if (USERPROFILE.getCurrentRoles().indexOf('provider') != -1) {
            var div;
            $.template('providerTabsTemplate', $('#provider_tabs_template'));
            $.tmpl('providerTabsTemplate', {}).appendTo('.nav-tabs');

            div = $('<div></div>').addClass('tab-pane').attr('id', 'provided-tab');
            $('<div></div>').attr('id', 'provided-content').appendTo(div);
            div.appendTo('.tab-content');
        } else {
            // Include the 'become a provider' button if needed
            if (USERPROFILE.getCurrentOrganization() == USERPROFILE.getUsername()) {
                var provBtn = $('<input></input>').addClass('btn btn-blue').attr('type', 'button').attr('id', 'become-prov');
                if (!USERPROFILE.providerRequested()) {
                    var requestForm = new ProviderRequestForm(USERPROFILE);

                    provBtn.val('Become a provider');
                    provBtn.click(function() {
                        requestForm.display();
                    })
                } else {
                    provBtn.val('Request pending');
                }
                provBtn.appendTo('.nav-tabs');
            }
        }

        if ($('#create-app').length > 0) {
            $('#create-app').click(function () {
                getRepositories(showCreateAppForm);
            });
            $('#register-res').click(showRegisterResourceForm);
            $('#view-res').click(function() {
                var resForm, offElem = {}
                offElem.getResources = function() {
                    return [];
                }
                resForm = new BindResourcesForm(offElem, true);
                resForm.display();
            });
        }

        // Load data into the tabs on show
        $('a[data-toggle="tab"]').on('shown', function (e) {
            changeTab(e.target.hash, true);
        });

        $('#number-offerings').change(function() {
            changeTab(currentTab);
        });

        $('#sorting').change(function() {
            changeTab(currentTab);
        });

        $('#cat-search').click(function() {
            var keyword = $.trim($('#cat-search-input').val());
            if (keyword != ''){
                searchParams.keyword = keyword;
                searchParams.searching = true;
                changeTab(currentTab);
            }
        });

        // Set listener for enter key
        $('#cat-search-input').keypress(function(e) {
            var keyword = $.trim($('#cat-search-input').val());

            if (e.which == 13 && keyword != '') {
                e.preventDefault();
                e.stopPropagation();
                searchParams.keyword = keyword;
                searchParams.searching = true;
                changeTab(currentTab);
            }
        });
        $('#cat-all').click(function() {
            changeTab(currentTab, true);
        });

        if (USERPROFILE.getUserRoles().indexOf('admin') == -1) {
            // The navigation menu width depends on the presence of the FI-LAB bar
            if ($('#oil-nav').length > 0) {
                $('.navigation').css('width', '188px');
            } else {
                $('.navigation').css('width', '278px');
            }
        }
        calculatePositions();
        changeTab('#purchased-tab');
    };

    getCurrentTab = function getCurrentTab () {
        return currentTab;
    };

    refreshView = function refreshView() {
        $('#catalogue-container').empty();
        paintCatalogue();
    };

    setFooter = function setFooter() {
        // Append the terms and conditions bar
        // Check if the bar is included
        if ($('footer').length > 0) {
            $('footer').remove();
        }
        // Create the new footer
        $.template('footerTemplate', $('#footer_template'));
        $.tmpl('footerTemplate').appendTo('body');
        if ($(window).height() < $(document).height()) {
            $('footer').css('position', 'absolute').css('top', ($(document).height()) + 'px');
        } else {
            $('footer').css('position', 'absolute').css('top', ($(document).height() - 30) + 'px');
        }
    }

    calculatePositions = function calculatePositions() {
        var position;

        $('.catalogue-form .form').removeAttr('style');

        // Check window width
        if ($(window).width() < 981) {
            // Change headers position to avoid problems with bootstrap responsive
            // FIX ME: This positions are valid if the FI-LAB bar is included
            $('.title_wrapper').css('top', '-30px');
            $('.navigation').css('top', '-109px');

            //Up the catalogue tabs
            if ($(window).width() < 769) { // Responsive activation
                $('.offerings-container').css('top', '225px');
                $('.offerings-container').css('left', '10px');
                $('.catalogue-form .form').css('width', '100%');
            } else {
                $('.offerings-container').css('top', '0');
                $('.offerings-container').css('left', '228px');
            }
        } else {
            $('.title_wrapper').css('top', '140px');
            $('.navigation').css('top', '60px');
            $('.offerings-container').css('top', '176px');
            $('.offerings-container').css('left', '228px');
        }
        // Calculate tabs width, at the end to avoid problems with position changes
        position = $('.tabbable').offset();
        $('.offerings-container').css('width', ($(window).width() - position.left) + 'px');
        setFooter();
    }

    $(window).resize(calculatePositions);

})();
