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

    var displayPurchaseInfo = function displayPurchaseInfo() {
        var offeringElement;

        // Create the offering Element
        offeringElement = new OfferingElement(OFFERING_INFO);

        // Display offering details view
        paintOfferingDetails(offeringElement, null, $('#remote-container'));

        // Remove unnecessary buttons and listeners
        $('#main-action').remove();
        $('h2:contains(Advanced operations)').remove();
        $('#advanced-op').remove();
        $('h2:contains(Comments)').remove();
        $('#back').remove();

        // Display purchase form
        purchaseOffering(offeringElement);

        // Replace the event handler in order to remove created components
        $('#message').on('hidden', function(evnt) {
            evnt.stopPropagation();
            evnt.preventDefault();
            $('#message-container').empty();
            $('#back').remove();
        });
    }

    $(document).ready(displayPurchaseInfo)
})();