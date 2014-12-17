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

    /**
     * Modal form used to create offering reviews
     * @param offeringElement object containing the offering to be reviewed
     * @param callerObj instance that creates the object, used for notifications
     * @param revData data of the review used for updates
     */
    CommentForm = function CommentForm(offeringElement, callerObj, revData) {
        this.offeringElement = offeringElement;
        this.callerObj = callerObj;
        this.rating = 0;
        this.reviewData = revData;
    }

    /**
     * Make the server request. Create and Update
     * @param request, Data to be sent
     */
    CommentForm.prototype.makeRequest = function makeRequest(request) {
        var client;
        var endpoint = 'REVIEW_COLLECTION';
        var clientMethod;

        var offeringContext = {
            'organization': this.offeringElement.getOrganization(),
            'name': this.offeringElement.getName(),
            'version': this.offeringElement.getVersion()
        };

        // Get the endpoint depending if it is a creation or an update
        if (this.reviewData) {
            endpoint = 'REVIEW_ENTRY';
            offeringContext.review = this.reviewData.id;
        }

        // Build the server client
        client = new ServerClient(endpoint, '');

        // Select method request
        if (this.reviewData) {
            clientMethod = client.update.bind(client);
        } else {
            clientMethod = client.create.bind(client);
        }

        //Make the request
        clientMethod(request, function() {
            $('#message').modal('hide');
            this.callerObj.refreshAndUpdateDetailsView();
        }.bind(this), offeringContext, function(xhr) {
            var resp = xhr.responseText;
            var msg = JSON.parse(resp).message;
            $('#message').modal('hide');
            MessageManager.showMessage('Error', msg);
        });
    };

    /**
     * Validate form fields.
     */
    CommentForm.prototype.validateFields = function validateFields() {
        var csrfToken = $.cookie('csrftoken');
        var title, comment, request = {};
        var error = false;
        var msg;

        title = $.trim($('#comment-title').val());
        comment = $.trim($('#comment-text').val());

        // Check that required fields contains a value
        if (!title || ! comment) {
            error = true;
            msg = 'Missing required field(s):';
            if (!title) {
                msg += ' Title';
            }
            if (!comment) {
                msg += ' Comment';
            }
        }

        // Check the length of the comment
        if (!error && comment.length > 1000) {
            error = true;
            msg = 'The comment cannot contain more than 1000 characters';
        }

        // If the fields are correctly filled make the request
        if (!error) {
            request.title = title;
            request.comment = comment;
            request.rating = this.rating;

            this.makeRequest(request);
        } else {
            MessageManager.showAlertError('Error', msg, $('#error-message'));
        }
    };

    /**
     * Paint the form and includes values if making an update
     */
    CommentForm.prototype.paintCommentForm = function painCommentForm() {
        var stars;

        MessageManager.showMessage('Review', '');

        $('<div></div>').attr('id', 'error-message').appendTo('.modal-body');
        $('<div></div>').addClass('clear').appendTo('.modal-body');

        $('<p></p>').text('Rating').appendTo('.modal-body');

        stars = $('<div></div>').appendTo('.modal-body');

        // Create stars listeners for getting the rating value
        for (var i = 0; i < 5; i++) {

            // Lister for fill the stars on hover
            var icon = $('<i></i>').addClass('icon-star-empty').attr('id', 'star-' + i).on('hover', (function(pos, self) {
                return function() {
                    // Unfill stars
                    for (var k = 0; k < self.rating; k ++) {
                        $('#star-' + k).removeClass('icon-star blue-star').addClass('icon-star-empty');
                    }

                    // fill hover stars
                    for (var k = 0; k < pos + 1; k++) {
                        $('#star-' + k).removeClass('icon-star-empty').addClass('icon-star blue-star');
                    }
                }
            })(i, this));

            // Listener for getting the rating value on click
            icon.click((function(pos, self) {
                return function() {
                    self.rating = pos + 1;
                }
            })(i, this));

            // listener for filling the stars depending on the current selected rating
            icon.mouseout((function(pos, self) {
                return function() {
                    // Unfill not rated stars
                    for (var k = 0; k < pos + 1; k++) {
                        $('#star-' + k).removeClass('icon-star blue-star').addClass('icon-star-empty');
                    }
                    // Fill rated stars
                    for (var k = 0; k < self.rating; k ++) {
                        $('#star-' + k).removeClass('icon-star-empty').addClass('icon-star blue-star');
                    }
                }
            })(i, this));

            icon.appendTo(stars);
        }

        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        $('<p></p>').text('Title').appendTo('.modal-body');
        $('<input></input>').attr('type', 'text').attr('placeholder', 'Title').attr('id', 'comment-title').appendTo('.modal-body');
        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        $('<p></p>').text('Comment').appendTo('.modal-body');
        $('<textarea></textarea>').attr('id', 'comment-text').appendTo('.modal-body');

        // Fill fields if review data has been provided
        if (this.reviewData) {
            for (var i = 0; i < this.reviewData.rating; i++) {
                $('#star-' + i).removeClass('icon-star-empty').addClass('icon-star blue-star');
            }
            this.rating = this.reviewData.rating;

            $('#comment-title').val(this.reviewData.title);
            $('#comment-text').val(this.reviewData.comment);
        }

        $('.modal-footer > .btn').click(function(evt) {
            evt.stopPropagation();
            evt.preventDefault();
            this.validateFields();
        }.bind(this));
    };

})();
