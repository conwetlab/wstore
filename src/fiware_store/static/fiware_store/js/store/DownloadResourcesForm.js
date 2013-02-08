
(function() {

    downloadElements = function downloadElements (offeringElement) {
        var resources = offeringElement.getResources();

        MessageManager.showMessage('Download', '');

        $('<h2></h2>').text('Invoice').appendTo('.modal-body');
        $('<a></a>').text('Download invoice').click(function () {
            window.open(offeringElement.getBillPath());
        }).appendTo('.modal-body');

        $('<h2></h2>').text('Resources').appendTo('.modal-body');
        for (var i = 0; i < resources.length; i++) {
            p = $('<p></p>');
            $('<a></a>').text(resources[i].name).click((function(res) {
                return function () {
                    window.open(res.link);
                };
            })(resources[i])).appendTo(p)

            p.appendTo('.modal-body');

        }

    };

})(); 
