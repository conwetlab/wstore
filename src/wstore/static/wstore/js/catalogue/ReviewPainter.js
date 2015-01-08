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
     * Painter class in charge of painting the reviews associates with an offering
     */
    ReviewPainter = function ReviewPainter(offeringElement, container, callerObj) {
        // Build reviews endpoint
        var endp = EndpointManager.getEndpoint('REVIEW_COLLECTION', {
            'organization': offeringElement.getOrganization(),
            'name': offeringElement.getName(),
            'version': offeringElement.getVersion()
        });

        this.offeringElement = offeringElement;
        this.container = container;
        this.reviewTemplate = $('#reviews_template');
        this.commentTemplate = $('#comment_template');

        this.client = new ServerClient('', endp, true);
        this.extended = false;
        this.prevScrollPos = 0;
        this.callerObj = callerObj;
    };

    /**
     * Handler of th exapnd button to unexpand
     */
    var resizeHandlerDecrease = function resizeHandlerDecrease(self) {
        $(document).stop();

        $('.btn-resize').removeAttr('style');
        $('#comments').removeAttr('style');
        self.scrollPag.removeListeners();
        $('#comments').empty();
        self.scrollPag.getNextPage();

        $('.btn-resize').empty();
        $('.btn-resize').append('<i class="icon-plus"></i>  View More');
        $('.btn-resize').off('click');
        $('.btn-resize').click(function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            resizeHandlerIncrease(this);
        }.bind(self));
        self.extended = false;
    };

    var resizeHandlerIncrease = function resizeHandlerIncrese(self) {
        var newPos;
        var found = false;

        self.scrollPag.createListeners();
        $('#comments').css('height', 'auto');

        $('.btn-resize').empty();
        $('.btn-resize').append('<i class="icon-minus"></i>  View Less');
        $('.btn-resize').off('click');
        $('.btn-resize').click(function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            resizeHandlerDecrease(this);
        }.bind(self));
        self.extended = true;
    };

    /**
     * Handler for the scroll event
     */
    ReviewPainter.prototype.scrollHandler = function scrollHandler(evnt) {
        if (this.extended) {
            if ($('.btn-resize').offset().top  <= $('h2:contains(Reviews)').offset().top){
                $('.btn-resize').removeAttr('style');
            } else if (($('.btn-resize').offset().top <= $('#options-bar').offset().top + 50)
                    && !$('.btn-resize').attr('style')) {

                var rightPos = ($(window).width() - ($('.btn-resize').offset().left + $('.btn-resize').outerWidth()));
                $('.btn-resize').css('right', rightPos);
                $('.btn-resize').css('top', '100px');
                $('.btn-resize').css('position', 'fixed');
            }
        }
    };

    /**
     * Create review listeners
     */
    ReviewPainter.prototype.setListeners = function setListeners() {
        // Create scroll pagination
        this.scrollPag = new ScrollPagination($(document), $('#main-tab'), this.paintComments.bind(this), this.client, this.scrollHandler.bind(this), $('#comments'));
        this.scrollPag.configurePaginationParams(360, 3);

        // Show review button if needed
        if (this.offeringElement.getState() == 'purchased' ||
            (this.offeringElement.getState() == 'published' && 
             this.offeringElement.isOpen() && !USERPROFILE.isOwner(this.offeringElement))) {

            $('#comment-btn').removeClass('hide').click((function() {
                var commentForm = new CommentForm(this.offeringElement, this.callerObj);
                commentForm.paintCommentForm();
            }).bind(this));
        }
        // Set expand listener
        $('.btn-resize').click(function() {
            resizeHandlerIncrease(this);
        }.bind(this));
    };

    ReviewPainter.prototype.checkExpand = function checkExpand() {
     // Check if it is the first page
        if (this.scrollPag.getNextPageNumber() == 2) {
            // Check if the expand button if needed (More than 2 rows)
            var elemsRow = this.scrollPag.getElementsRow();
            var lastPageLen = this.scrollPag.getLastPageLen();

            if (lastPageLen > (elemsRow*2)) {
                $('.btn-resize').removeClass('hide');
            } else {
                $('.btn-resize').addClass('hide');
            }
        }

    }

    /**
     * Check if the current user is owner of a review
     */
    var isReviewer = function isReviewer(self, review) {
        var isOwner = false;
        if (USERPROFILE.getCurrentOrganization() === review.organization &&
                (USERPROFILE.getUsername() === review.user || ORGANIZATIONPROFILE.isManager())) {
            isOwner = true;
        }
        return isOwner;
    };

    var editHandler = function editHandler(review) {
        // Build a comment form
        var commentForm = new CommentForm(this.offeringElement, this.callerObj, {
            'id': review.id,
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment
        });
        commentForm.paintCommentForm();
    };

    var deleteHandler = function deleteHandler(review) {
        var msg = 'Are you sure that you want to remove your review';
        MessageManager.showYesNoWindow(msg, function() {
            var client = new ServerClient('REVIEW_ENTRY', '');
            context = {
                'review': review.id,
                'organization': this.offeringElement.getOrganization(),
                'name': this.offeringElement.getName(),
                'version': this.offeringElement.getVersion()
            }
            client.remove(this.callerObj.refreshAndUpdateDetailsView.bind(this.callerObj), context);
        }.bind(this), 'Remove');
    };

    var replyHandler = function replyHandler(review) {
        var commentForm = new CommentForm(this.offeringElement, this.callerObj, {'id': review.id}, true);
        commentForm.paintCommentForm();
    }

    /**
     * Build the options of a selected review
     */
    var buildOptions = function buildOptions(self, review, domElem) {
        var container = domElem.find('.comment-options');

        container.addClass('hide');

        // Check if the user is owner of the offering
        if (USERPROFILE.isOwner(self.offeringElement) && !review.response) {
            var reply = $('<a rel="tooltip" title="Reply" class="btn btn-blue"><i style="margin-left: -2px;" class="icon-reply"></i></a>').click(replyHandler.bind(self, review));
            container.append(reply);
        } else if(isReviewer(self, review)) { // Check if the user is the reviewer of the offering
            // Include reviewer options
            var edit = $('<a rel="tooltip" title="Edit review" class="btn btn-blue"><i class="icon-edit"></i></a>').click(editHandler.bind(self, review));
            var del = $('<a rel="tooltip" title="Remove review" class="btn btn-blue"><i class="icon-trash"></i></a>').click(deleteHandler.bind(self, review));
            container.append(edit);
            container.append(del);
        }
    };

    var buildReviewClickHandler = function buildReviewClickHandler(self, response) {
        var closeSelected = function(elems) {
            var responseDiv;
            elems.removeAttr('style');
            elems.find('.txt-gradient').removeClass('hide');
            elems.find('.txt-gradient').css('visibility', 'hidden');
            elems.removeClass('comment-selected');

            elems.find('.comment-options').addClass('hide');

            setTimeout(function() {
                responseDiv  = elems.find('.comment-reply-dec');
                responseDiv.css('display', 'none');
                elems.find('.up-marker').css('display', 'none');
                elems.find('.txt-gradient').removeAttr('style');
            }, 1000);
        };

        return function() {
            if ($(this).attr('style')) {
                closeSelected($(this));
                if (!self.extended) {
                    setTimeout(function() {
                        $('#comments').removeAttr('style');
                    }, 1000);
                }
            } else {
                closeSelected($(this).parent().find('.comment-selected'));
                // Calculate text height
                var size = $(this).find('p').height() + 80;

                $(this).addClass('comment-selected');

                if (response) {
                    var responseSize;
                    var responseDiv  = $(this).find('.comment-reply-dec');

                    $(this).find('.up-marker').removeAttr('style');

                    responseDiv.removeAttr('style');
                    responseSize = responseDiv.find('p').height() + 80;
                    responseDiv.css('height', responseSize + 'px');
                    size += responseSize;
                }

                $(this).css('height', size + 'px');

                if (!self.extended) {
                    $('#comments').css('height', 'auto');
                };
                $(this).find('.txt-gradient').addClass('hide');
                $(this).find('.comment-options').removeClass('hide');
            }
        };
    };

    /**
     * Private method use to render the template of a concrete comment or
     * reply
     */
    var createCommentTemplate = function createCommentTemplate (self, comment, isReply) {
        var templ;
        var username = comment.organization;

        if (username != comment.user) {
            username += ' (' + comment.user + ')';
        }
        $.template('commentTemplate', $('#comment_template'));
        templ = $.tmpl('commentTemplate', {
            'user': username,
            'timestamp': comment.timestamp.split(' ')[0],
            'title': comment.title
        })

        if (!isReply) {
            templ.click(buildReviewClickHandler(self, comment.response));
        }

        // ---- //
        var reviewText = templ.find('.review-text');
        var repText = comment.comment.split('\n').join('<br />');
        reviewText[0].innerHTML = repText;

        return templ;
    };

    /**
     * Paint comments
     * @param comments, list with the comments to be painted
     */
    ReviewPainter.prototype.paintComments = function paintComments(comments) {
        this.checkExpand();

        // Clear comments if needed
        if (this.scrollPag.getNextPageNumber() == 2) {
            $('#comments').empty();
        }
        
        // Paint comments
        for (var i = 0; i < comments.length; i++) {
            var templ = createCommentTemplate(self, comments[i], false);

            // Build the different options for the review
            buildOptions(this, comments[i], templ);

            fillStarsRating(comments[i].rating, templ.find('.comment-rating'));

            if (comments[i].response) {
                var size;
                var response = comments[i].response
                response.comment = response.response;

                var responseTempl = createCommentTemplate(this, comments[i].response, true);
                responseTempl.addClass('comment-reply-dec').css('display', 'none');
                responseTempl.find('.txt-gradient').remove();

                var marker = $('<div class="up-marker"></div>').css('display', 'none') ;
                templ.append(marker);
                templ.append(responseTempl);
            }
            templ.appendTo('#comments');
        }
    };

    /**
     * Paint offerings reviews
     */
    ReviewPainter.prototype.paint = function paint() {
        var comments = this.offeringElement.getComments();

        $.template('reviewTemplate', this.reviewTemplate);
        $.tmpl('reviewTemplate', {
            'score': this.offeringElement.getRating(),
            'votes': comments.length
        }).appendTo(this.container);

        this.setListeners();
        this.scrollPag.getNextPage();
    };
})();