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
        var organizationForm = new OrganizationForm();
        var userForm = new UserForm();
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
            organizationForm.elementInfoRequest();
        });

        $('.show-prof').click(function() {
            userForm.elementInfoRequest();
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
            organizationForm.paintForm();
        });

        $('.add-prof').click(function() {
            userForm.paintForm();
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
        var position;
        var filabInt = $('#oil-nav').length > 0;

        $('.admin-element').removeAttr('style');
        // Check window width
        if (filabInt) {
            if ($(window).width() < 981) {
                $('.title_wrapper').css('top', '-30px');
                $('.navigation').css('top', '-109px');
                $('.admin-element').css('top', '-60px');
            } else {
                var offset;
                var width;  
                $('.title_wrapper').css('top', '140px');
                $('.navigation').css('top', '60px');
            }
        }
        // Fixed position in admin view
        offset = $(window).height() - $('.admin-element').offset().top - 30;
        width = $(window).width() - $('.admin-element').offset().left -10;
        $('.admin-element').css('height', offset.toString() + 'px');
        $('.admin-element').css('width', width.toString() + 'px');

        // Check username length to avoid display problems
        if ($.trim($('div.btn.btn-blue > div.dropdown-toggle span').text()).length > 12) {
            var shortName = ' '+ USERPROFILE.getCompleteName().substring(0, 9) + '...';
            // Replace user button contents
            var userBtn = $('div.btn.btn-blue > div.dropdown-toggle span');
            userBtn.empty();
            userBtn.text(shortName);
      }
    }
    $(window).resize(calculatePositions);
})()
