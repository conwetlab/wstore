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

    ReviewPainter = function ReviewPainter(offeringElement, container) {
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
    };

    var resizeHandlerDecrease = function resizeHandlerDecrease(self) {
        $('.tab-content').stop();

        $('.btn-resize').removeAttr('style');
        $('.tab-content').animate({
            scrollTop: self.prevScrollPos
        }, 1500, function() {
            $('#comments').removeAttr('style');
            this.scrollPag.removeListeners();
            $('#comments').empty();
            this.scrollPag.getNextPage();
        }.bind(self));

        $('.icon-resize-horizontal').off('click');
        $('.icon-resize-horizontal').click(function(evnt) {
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

        self.prevScrollPos = $('.tab-content').scrollTop();
        $('#comments').css('height', 'auto');
        $('.tab-content').stop();

        $('.tab-content').animate({
            scrollTop: $('.tab-content').scrollTop() + 100
        }, 1500);

        $('.icon-resize-horizontal').off('click');
        $('.icon-resize-horizontal').click(function(evnt) {
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
            if (($('.btn-resize').offset().top <= $('h2:contains(Reviews)').offset().top)){
                $('.btn-resize').removeAttr('style');
            } else if (($('.btn-resize').offset().top <= $('.tab-content').offset().top + 30)) {
                $('.btn-resize').css('left', $('.btn-resize').offset().left);
                $('.btn-resize').css('top', $('.tab-content').offset().top + 30);
                $('.btn-resize').css('position', 'fixed');
            }
        }
    };

    /**
     * Create review listeners
     */
    ReviewPainter.prototype.setListeners = function setListeners() {
        // Create scroll pagination
        this.scrollPag = new ScrollPagination($('.tab-content'), $('#main-tab'), this.paintComments, this.client, this.scrollHandler.bind(this), $('#comments'));
        this.scrollPag.configurePaginationParams(360, 3);

        // Show review button if needed
        if (this.offeringElement.getState() == 'purchased') {
            $('#comment-btn').removeClass('hide').click((function() {
                paintCommentForm(this.offeringElement, this);
            }).bind(this));
        }
        // Set expand listener
        $('.btn-resize').click(function() {
            resizeHandlerIncrease(this);
        }.bind(this));
    };

    /**
     * Paint comments
     * @param comments, list with the comments to be painted
     */
    ReviewPainter.prototype.paintComments = function paintComments(comments) {
        for (var i = 0; i < comments.length; i++) {
            var templ;

            $.template('commentTemplate', $('#comment_template'));
            templ = $.tmpl('commentTemplate', {
                'user': comments[i].user,
                'timestamp': comments[i].timestamp.split(' ')[0],
                'title': comments[i].title,
                'comment': comments[i].comment
            });

            fillStarsRating(comments[i].rating, templ.find('.comment-rating'));
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