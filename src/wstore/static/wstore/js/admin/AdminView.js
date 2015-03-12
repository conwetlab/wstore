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

(function () {

    var referrer;

    // Repaint initial table
    paintElementTable = function paintElementTable () {
        $('#admin-container').empty();
        $.template('adminElemTemplate', $('#admin_elem_template')); // Create the template
        $.tmpl('adminElemTemplate').appendTo("#admin-container"); // Render and append the template

        var unitForm = new UnitsForm();
        var rssForm = new RssForm();
        var organizationForm = new OrganizationForm();
        var userForm = new UserForm();
        var marketplaceForm = new MarketplaceForm();
        var repositoryForm = new RepositoryForm();
        var currencyForm = new CurrencyForm();

        $('.show-markets').click(function() {
            marketplaceForm.elementInfoRequest();
        });

        $('.show-rep').click(function() {
            repositoryForm.elementInfoRequest();
        });

        $('.show-rss').click(function() {
            rssForm.elementInfoRequest();
        });

        $('.show-org').click(function() {
            organizationForm.elementInfoRequest();
        });

        $('.show-prof').click(function() {
            userForm.elementInfoRequest();
        });

        $('.show-units').click(function() {
           unitForm.elementInfoRequest();
        });

        $('.show-currencies').click(function() {
            currencyForm.elementInfoRequest();
        });

        $('.add-market').click(function() {
            marketplaceForm.paintForm();
        });

        $('.add-rep').click(function() {
            repositoryForm.paintForm();
        });

        $('.add-rss').click(function() {
            rssForm.paintForm();
        });

        $('.add-org').click(function() {
            organizationForm.paintForm();
        });

        $('.add-prof').click(function() {
            userForm.paintForm();
        });

        $('.add-unit').click(function() {
            unitForm.paintForm();
        });

        $('.add-currency').click(function() {
            currencyForm.paintForm();
        });
        // Set back button
        if (!referrer) {
            var splref;

            referrer = document.referrer;
            splref = referrer.split('/');
            // Check if the page has been reloaded or called from an external source
            if (splref[splref.length - 1] == 'administration' ||
                    (splref[splref.length - 1] == '' && splref[splref.length - 2] == 'administration') ||
                    splref[2] != document.baseURI.split('/')[2]) {
                referrer = '/';
            }
        }
        $('#back').off('click');
        $('#back').attr('href', referrer);
    };

    calculatePositions = function calculatePositions() {
        var position;
        // Fixed position in admin view
        offset = $(window).height() - $('.admin-element').offset().top - 30;
        $('.admin-element').css('height', offset.toString() + 'px');

    }
    $(window).resize(calculatePositions);
})()
