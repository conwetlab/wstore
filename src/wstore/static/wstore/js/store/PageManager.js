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

    PageManager = function PageManager() {
        this.pages = {
            'home': this.loadHomePage.bind(this),
            'offerings': this.loadOfferingsPage.bind(this),
            'keyword': this.loadSearchKeywordPage.bind(this),
            'tag': this.loadSearchTagPage.bind(this),
            'details': this.loadDetailsPage.bind(this)
        };
    };

    var createMenuPainter = function createMenuPainter() {
        var mpainter = new MenuPainter(setServiceHandler, setDataHandler, setWidgetHandler);
        setMenuPainter(mpainter);
    }

    var loadSearchPage = function loadSearchPage(title, endpoint, text) {
        createMenuPainter();
        $('<div class="clear space" /><div class="row-fluid" id="store-container"></div>').appendTo('#home-container');
        searchView = new StoreSearchView();
        setSearchView(searchView);
        searchView.setTitle(title);

        if (!text) {
            searchView.initSearchView(endpoint);
        } else {
            searchView.initSearchView(endpoint, text);
        }
    };

    PageManager.prototype.loadHomePage = function loadHomePage() {
        $('#home-container').empty();
        paintHomePage();
    };

    PageManager.prototype.loadOfferingsPage = function loadOfferingsView() {
        loadSearchPage('Offerings', 'OFFERING_COLLECTION');
    };

    PageManager.prototype.loadSearchKeywordPage = function loadSearchKeywordPage() {
        $('#text-search').val(INIT_INFO);
        loadSearchPage('Offerings', 'SEARCH_ENTRY');
    };

    PageManager.prototype.loadSearchTagPage = function loadSearchTagPage() {
        var tag = INIT_INFO;
        var title = tag;

        if (tag == 'service') {
            title = 'Services';
        } else if (tag == 'dataset') {
            title = 'Datasets';
        } else if (tag == 'widget') {
            title = 'Widgets / Mashups';
        }
        
        loadSearchPage(title, 'SEARCH_TAG_ENTRY', tag);
    };

    PageManager.prototype.loadDetailsPage = function loadDetailsPage() {
        createMenuPainter();

        // Create offering element
        var offeringElem = new OfferingElement(INIT_INFO);
        var catDetailsView = new CatalogueDetailsView(offeringElem, function() {
            paintHomePage();
            openMenuPainter();
        }, '#home-container');

        catDetailsView.showView();
    };

    PageManager.prototype.getPageLoader = function getPageLoader(page) {
        return this.pages[page];
    };
})();
