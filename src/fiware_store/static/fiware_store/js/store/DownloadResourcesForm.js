
(function() {

    downloadElements = function downloadElements (offeringElement) {
        var resources = offeringElement.getResources();

        MessageManager.showMessage('Download', '');

        $('<h2></h2>').text('Invoices').appendTo('.modal-body');

        for (var i = 0; i < offeringElement.getBillPath().length; i++) {
            var path_elem = offeringElement.getBillPath()[i];
            var p = $('<p></p>');
            var date = path_elem.split("_")[1];

            date = date.split(".")[0];

            $('<a></a>').text(date).click((function (path) {
                return function () {
                    window.open(path);
                };
            })(path_elem)).appendTo(p);

            p.appendTo('.modal-body');
        }

        $('<h2></h2>').text('Resources').appendTo('.modal-body');
        for (var i = 0; i < resources.length; i++) {
            var p = $('<p></p>');
            $('<a></a>').text(resources[i].name).click((function(res) {
                return function () {
                    window.open(res.link);
                };
            })(resources[i])).appendTo(p);

            p.appendTo('.modal-body');

        }

    };

})(); 
