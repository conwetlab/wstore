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

    ServerClient = function ServerClient(entryURL, collectionURL) {
        this.entryURL = entryURL;
        this.collectionURL = collectionURL;
    };

    /**
     * Private method that makes requests to the server
     * @param self, Class object equivalent to this
     * @param method, http method: GET, POST, PUT, DELETE
     * @param callback, funtion to be called on success
     * @param data, JSON data for PUT and POST request
     * @param elemDict, Object used for URL rendering if needed
     */
    var request = function request(self, method, callback, data, elemDict) {
        var url;
        var csrfToken = $.cookie('csrftoken');

        // Select endpoint
        if ($.isEmptyObject(elemDict)) {
            url = EndpointManager.getEndpoint(self.collectionURL);
        } else {
            url = EndpointManager.getEndpoint(self.entryURL, elemDict);
        }

        // Make request
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: method,
            url: url,
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function (response) {
                if (method == 'GET') {
                    callback(response);
                } else {
                    callback();
                }
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    /**
     * Makes a GET request
     * @param callback, Function to be called on success
     * @param elemDict, Object used for URL rendering if needed
     */
    ServerClient.prototype.get = function get(callback, elemDict) {
        request(this, 'GET', callback, '', elemDict);
    };

    /**
     * Make generic POST request to the collection URL
     * @param data, JSON info to be sent
     * @param callback, Function to be called on success
     */
    ServerClient.prototype.create = function create(data, callback, elemDict) {
        var cont = {};
        if (elemDict) {
            cont = elemDict;
        }
        request(this, 'POST', callback, data, cont);
    };

    /**
     * Make a PUT request
     * @param data, JSON info to be sent
     * @param callback, Function to be called on success
     * @param elemDict, Object used for URL rendering if needed
     */
    ServerClient.prototype.update = function update(data, callback, elemDict) {
        request(this, 'PUT', callback, data, elemDict);
    };

    /**
     * Make a DELETE request
     * @param callback, Function to be called on success
     * @param elemDict, Object used for URL rendering if needed
     */
    ServerClient.prototype.remove = function remove(callback, elemDict) {
        request(this, 'DELETE', callback, '', elemDict);
    };
})();