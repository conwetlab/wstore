(function() {

    var rating = 0;
    var caller;

    var makeCreateCommentRequest = function makeCreateCommentRequest(offElement) {
        var csrfToken = $.cookie('csrftoken');
        var title, comment, request = {};
        var error = false;
        var msg;

        var offeringContext = {
            'organization': offElement.getOrganization(),
            'name': offElement.getName(),
            'version': offElement.getVersion()
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
        if (!error && comment.length > 200) {
            error = true;
            msg = 'The comment cannot contain more than 200 characters';
        }

        // If the fields are correctly filled make the request
        if (!error) {
            request.title = title;
            request.comment = comment;
            request.rating = rating;

            $('#loading').removeClass('hide');  // Loading view when waiting for requests
            $('#loading').css('height', $(window).height() + 'px');
            $('#message').modal('hide');
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "POST",
                url: EndpointManager.getEndpoint('RATING_ENTRY', offeringContext),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    $('#loading').addClass('hide');
                    $('#message').modal('hide');
                    caller.refreshAndUpdateDetailsView();
                },
                error: function (xhr) {
                    $('#loading').addClass('hide');
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showAlertError('Error', msg, $('#error-message'));
        }
    };

    paintCommentForm = function painCommentForm(offElement, callerObj) {
        var stars;

        caller = callerObj;
        MessageManager.showMessage('Comment', '');

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
            makeCreateCommentRequest(offElement);
        });
    };

})();
