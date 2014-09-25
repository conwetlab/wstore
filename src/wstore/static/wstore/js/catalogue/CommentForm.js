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

    CommentForm = function CommentForm(offeringElement, callerObj) {
        this.offeringElement = offeringElement;
        this.callerObj = callerObj;
        this.rating = 0;
    }

    CommentForm.prototype.makeCreateCommentRequest = function makeCreateCommentRequest() {
        var csrfToken = $.cookie('csrftoken');
        var title, comment, request = {};
        var error = false;
        var msg;

        var offeringContext = {
            'organization': this.offeringElement.getOrganization(),
            'name': this.offeringElement.getName(),
            'version': this.offeringElement.getVersion()
        };

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
            var client = new ServerClient('REVIEW_COLLECTION', '');

            request.title = title;
            request.comment = comment;
            request.rating = rating;

            client.create(request, function() {
                $('#message').modal('hide');
                this.callerObj.refreshAndUpdateDetailsView();
            }.bind(this), offeringContext, function() {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                $('#message').modal('hide');
                MessageManager.showMessage('Error', msg);
            });

        } else {
            MessageManager.showAlertError('Error', msg, $('#error-message'));
        }
    };

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
            var icon = $('<i></i>').addClass('icon-star-empty').attr('id', 'star-' + i).on('hover', (function(pos) {
                return function() {
                    // Unfill stars
                    for (var k = 0; k < rating; k ++) {
                        $('#star-' + k).removeClass('icon-star blue-star').addClass('icon-star-empty');
                    }

                    // fill hover stars
                    for (var k = 0; k < pos + 1; k++) {
                        $('#star-' + k).removeClass('icon-star-empty').addClass('icon-star blue-star');
                    }
                }
            })(i));

            // Listener for getting the rating value on click
            icon.click((function(pos) {
                return function() {
                    rating = pos + 1;
                }
            })(i));

            // listener for filling the stars depending on the current selected rating
            icon.mouseout((function(pos) {
                return function() {
                    // Unfill not rated stars
                    for (var k = 0; k < pos + 1; k++) {
                        $('#star-' + k).removeClass('icon-star blue-star').addClass('icon-star-empty');
                    }
                    // Fill rated stars
                    for (var k = 0; k < rating; k ++) {
                        $('#star-' + k).removeClass('icon-star-empty').addClass('icon-star blue-star');
                    }
                }
            })(i));

            icon.appendTo(stars);
        }

        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        $('<p></p>').text('Title').appendTo('.modal-body');
        $('<input></input>').attr('type', 'text').attr('placeholder', 'Title').attr('id', 'comment-title').appendTo('.modal-body');
        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        $('<p></p>').text('Comment').appendTo('.modal-body');
        $('<textarea></textarea>').attr('id', 'comment-text').appendTo('.modal-body');

        $('.modal-footer > .btn').click(function(evt) {
            evt.stopPropagation();
            evt.preventDefault();
            this.makeCreateCommentRequest();
        }.bind(this));
    };

})();
