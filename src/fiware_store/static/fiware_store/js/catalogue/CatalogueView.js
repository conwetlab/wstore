
(function () {

    var currentTab;
    var currentPage = 1;
    var numberOfPages = 1;

    var getNextUserOfferings = function getNextUserOfferings (nextPage) {
        // Set the pagination values in catalogue search view
        setNextPage(nextPage);
        // refresh pagination element
        refreshPagination(nextPage);
        currentPage = nextPage;
        // make get offerings request
        getUserOfferings(currentTab, paintProvidedOfferings);
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

    var changeTab = function changeTab (tab) {
        currentTab = tab;
        getUserOfferings(tab, setPaginationParams, true);
    };

    paintCatalogue = function paintCatalogue() {
        // Get the catalogue template
        $.template('catalogueTemplate', $('#catalogue_search_template'));
        $.tmpl('catalogueTemplate', {}).appendTo('#catalogue-container');

        if ($('#create-app').length > 0) {
            $('#create-app').click(function () {
                getRepositories(showCreateAppForm);
            });
            $('#register-res').click(showRegisterResourceForm);
        }

        // Load data into the tabs on show
        $('a[data-toggle="tab"]').on('shown', function (e) {
            changeTab(e.target.hash);
        });

        $('#number-offerings').change(function() {
            changeTab(currentTab);
        });

        changeTab('#purchased-tab');

    };

    getCurrentTab = function getCurrentTab () {
        return currentTab;
    };

    $(document).ready(paintCatalogue);
})();
