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
     * Scroll based pagination component, paints pages using the scroll position
     * @param scrollCont, container that includes the sroll
     * @param content, Dom element that scrolls
     * @param painter, specific function for painting the element
     * @param client, client to retrieve the elements
     * @param scrollHandler, handler for scroll events in case that this event should include
     * different functionality from pagination.
     */
    ScrollPagination = function ScrollPagination(scrollCont, content, painter, client, scrollHandler, elemCont) {
        // Dom elements
        this.scrollContainer = scrollCont;
        this.content = content;
        this.painter = painter;
        this.client = client;
        this.scrollHandler = scrollHandler;

        this.elementContainer = elemCont
        if (!elemCont) {
            this.elementContainer = this.content;
        }

        // Default pagination params
        this.elementsPage = 10;
        this.nextPage = 1;
        this.numberOfRows = 3;
        this.elemSpace = 50;
        this.extraQuery = '';
    };

    /**
     * Set pagination params
     */
    ScrollPagination.prototype.configurePaginationParams = function configurePaginationParams(elementWidth, numberRows, extraQuery) {
        this.elementWidth = elementWidth;
        this.numberOfRows = numberRows;

        if (extraQuery) {
            this.extraQuery = extraQuery;
        }

        this.elementsPage = this.calculateElementsPage();
    };

    /**
     * Return the number of elements per row
     */
    ScrollPagination.prototype.getElementsRow = function getElementsRow() {
        var elementsRow = Math.floor((this.elementContainer.width() - this.elemSpace) / this.elementWidth);

        // If the width is fewer that an element
        // one element per row
        if (!elementsRow) {
            elementsRow = 1;
        }
        return elementsRow;
    };

    /**
     * Calculate the number of elements to be included per page
     * based on the width of the container and the width of the
     * elements
     */
    ScrollPagination.prototype.calculateElementsPage = function calculateElementsPage() {
        var elementsRow = this.getElementsRow();

        return elementsRow*this.numberOfRows;
    };

    /**
     * Handler for get elements response
     */
    ScrollPagination.prototype.getReqHandler = function getReqHandler(elements) {
        this.nextPage += 1;
        this.nLastPage = elements.length;
        this.painter(elements);
    };

    /**
     * Returns the length of the last page retrieved
     */
    ScrollPagination.prototype.getLastPageLen = function getLastPageLen() {
        return this.nLastPage;
    };

    /**
     * Returns the number of elements contained in the last page requested
     */
    ScrollPagination.prototype.getNextPageNumber = function getNextPageNumber() {
        return this.nextPage;
    };

    ScrollPagination.prototype.setElemSpace = function setElemSpace(elemSpace) {
        this.elemSpace = elemSpace;
    };

    /**
     * Retrieves next elements page
     */
    ScrollPagination.prototype.getNextPage = function getNextPage() {
        var queryString = '?start=' + (((this.nextPage- 1) * this.elementsPage) + 1);
        queryString += '&limit=' + this.elementsPage;
        queryString += this.extraQuery;

        this.client.get(this.getReqHandler.bind(this), '', queryString);
    };

    /**
     * Creates scroll listeners
     */
    ScrollPagination.prototype.createListeners = function createListeners() {

        // Create scroll listener
        this.scrollContainer.scroll(function(evnt) {
           if ((this.scrollContainer.height() + this.scrollContainer.scrollTop()) >= this.content.height()) {
               this.getNextPage();
           }
           this.scrollHandler(evnt);
        }.bind(this));
    };

    /**
     * Removes scroll listeners
     */
    ScrollPagination.prototype.removeListeners = function removeListeners() {
        this.scrollContainer.off('scroll');
        this.nextPage = 1;
    };
})();