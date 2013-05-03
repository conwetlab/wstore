(function() {

    paintSearchView = function paintSearchView(offerings) {
        var ret;

        // Check if the main page template has been destroyed and 
        // create it again if needed
        if ($('#store-search').length == 0) {
            $.template('homePageTemplate', $('#home_page_template'));
            $.tmpl('homePageTemplate',  {}).appendTo('#home-container');
            // Set search listeners
            $('#search').click(searchOfferings);
            $('#all').click(function() {
                getOfferings('OFFERING_COLLECTION', '', paintSearchView);
            })
        }

        $('#store-container').empty()

        ret = $('<a></a>').text('Return').appendTo('#store-container');
        ret.click(paintHomePage);

        $.template('storeSearchTemplate', $('#store_search_template'));
        $.tmpl('storeSearchTemplate').appendTo('#store-container');

        if (offerings.length > 0) {
            paintOfferings(offerings, $('.search-container'), function() {
                getOfferings('OFFERING_COLLECTION', '', paintSearchView);
            });
        } else {
            var msg = 'No offerings match with your search';
            MessageManager.showAlertInfo('No offerings', msg, $('.search-container'))
        }
    }
})();