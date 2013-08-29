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
