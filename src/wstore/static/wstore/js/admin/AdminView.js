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

    // Repaint initial table
    paintElementTable = function paintElementTable () {
        $('#admin-container').empty();
        $.template('adminElemTemplate', $('#admin_elem_template')); // Create the template
        $.tmpl('adminElemTemplate').appendTo("#admin-container"); // Render and append the template

        var unitForm = new UnitsForm();
        var rssForm = new RssForm();
        var marketplaceForm = EndpointFormBuilder('marketplace');
        var repositoryForm = EndpointFormBuilder('repository');

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
            orgInfoRequest(paintOrganizations);
        });

        $('.show-prof').click(function() {
            userInfoRequest();
        });

        $('.show-units').click(function() {
           unitForm.elementInfoRequest();
        });

        $('.show-currencies').click(function() {
            currencyInfoRequest();
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
            paintOrganizationForm();
        });

        $('.add-prof').click(function() {
            paintUserForm();
        });

        $('.add-unit').click(function() {
            unitForm.paintForm();
        });

        $('.add-currency').click(function() {
            paintCurrencyForm();
        });
    };

    refreshView = function refreshView() {
        paintElementTable();
        calculatePositions();
    };

    calculatePositions = function calculatePositions() {
        var filabInt = $('#oil-nav').length > 0;
        // Check window width
        if (filabInt) {
            if ($(window).width() < 981) {
                // Change headers position to avoid problems with bootstrap responsive
                $('.title_wrapper').css('top', '-30px');
                $('.navigation').css('top', '-109px');
            } else {
                $('.title_wrapper').css('top', '140px');
                $('.navigation').css('top', '60px');
            }
        }
        // Check username length to avoid display problems
        if ($.trim($('div.btn.btn-success > div.dropdown-toggle').text()).length > 12) {
            var shortName = ' '+ USERNAME.substring(0, 9) + '...';
            // Replace user button contents
            var userBtn = $('div.btn.btn-success > div.dropdown-toggle');
            userBtn.empty();
            userBtn.text(shortName);
            userBtn.prepend($('<i></i>').addClass('icon-user icon-white'));
            userBtn.append($('<b></b>').addClass('caret'));
        }
    }
    $(window).resize(calculatePositions);
})()
