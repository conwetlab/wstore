
(function() {

    downloadElements = function downloadElements (offeringElement) {
        var resources = offeringElement.getResources();

        MessageManager.showMessage('Download', '');
        for (var i = 0; i < resources.lenght; i++) {
            $('<a></a>').text(resources[i].name).click(function() {
                window.open(resources[i].link);
            });
        }

    };

})(); 
