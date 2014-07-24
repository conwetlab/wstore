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

        self.prevScrollPos = $('.tab-content').scrollTop();
        $('#comments').css('height', 'auto');
        $('.tab-content').stop();

        $('.tab-content').animate({
            scrollTop: $('.tab-content').scrollTop() + 100
        }, 1500);

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
            if (($('.btn-resize').offset().top <= $('h2:contains(Reviews)').offset().top)){
                $('.btn-resize').removeAttr('style');
            } else if (($('.btn-resize').offset().top <= $('.tab-content').offset().top + 30)
                    && !$('.btn-resize').attr('style')) {

                var rightPos = ($(window).width() - ($('.btn-resize').offset().left + $('.btn-resize').outerWidth()));
                $('.btn-resize').css('right', rightPos);
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
        this.scrollPag = new ScrollPagination($('.tab-content'), $('#main-tab'), this.paintComments.bind(this), this.client, this.scrollHandler.bind(this), $('#comments'));
        this.scrollPag.configurePaginationParams(360, 3);

        // Show review button if needed
        if (this.offeringElement.getState() == 'purchased' ||
            (this.offeringElement.getState() == 'published' && this.offeringElement.isOpen())) {

            $('#comment-btn').removeClass('hide').click((function() {
                paintCommentForm(this.offeringElement, this.callerObj);
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
     * Paint comments
     * @param comments, list with the comments to be painted
     */
    ReviewPainter.prototype.paintComments = function paintComments(comments) {
        this.checkExpand();

        // Paint comments
        for (var i = 0; i < comments.length; i++) {
            var templ;
            var username = comments[i].user;

            $.template('commentTemplate', $('#comment_template'));
            templ = $.tmpl('commentTemplate', {
                'user': username,
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