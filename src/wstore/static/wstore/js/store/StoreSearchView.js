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