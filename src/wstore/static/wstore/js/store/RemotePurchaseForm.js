
(function() {

    var displayPurchaseInfo = function displayPurchaseInfo() {
        var offeringJson, offeringElement;

        // Fix the offering info
        offeringJson = JSON.parse(OFFERING_INFO.replace(/&quot;/g, "\""));

        // Create the offering Element
        offeringElement = new OfferingElement(offeringJson);

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