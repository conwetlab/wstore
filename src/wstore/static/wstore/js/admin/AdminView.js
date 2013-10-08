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

    var main = false;

    adminInfoRequest = function adminInfoRequest(endpoint, title) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint(endpoint),
            dataType: "json",
            success: function (response) {
                paintElementList(response, endpoint, title);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    // Paint marketplaces or repository info
    paintElementList = function paintElementList(elementInfo, endpoint, title) {

        $('#admin-container').empty();

        if (elementInfo.length > 0) {

            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': title}).appendTo('#admin-container');

            $.template('elemTemplate', $('#element_template'));
            $.tmpl('elemTemplate', elementInfo).appendTo('#table-list');
            $('#back').click(paintElementTable);
            $('.add').click(function () {
                paintForm(endpoint, title);
            });
            $('.delete').click(function (event) {
                var clicked_elem = event.target;
                makeRemoveRequest(clicked_elem, endpoint, title)
            });
        } else {
            var msg = 'No ' + title + ' registered, you may want to register one'; 
            MessageManager.showAlertInfo(title, msg);
        }
    };

    makeRemoveRequest = function makeRemoveRequest(element, endpoint, title) {
        var name, jqObject, effectiveEndpoint, csfrToken;

        jqObject = jQuery(element);
        name = jqObject.parent().parent().parent().find('.elem-name').text();

        effectiveEndpoint = endpoint.replace('COLLECTION', 'ENTRY');;

        csrfToken = $.cookie('csrftoken');

        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "DELETE",
            url: EndpointManager.getEndpoint(effectiveEndpoint, {'name': name}),
            dataType: 'json',
            success: function (response) {
                adminInfoRequest(endpoint, title)
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    makeCreateRequest = function makeCreateRequest(endpoint, title) {
        var name, host;

        name = $.trim($('#elem-name').val());
        host = $.trim($('#elem-host').val());

        if (name && host) {
            var csrfToken = $.cookie('csrftoken');

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "POST",
                url: EndpointManager.getEndpoint(endpoint),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    'name': name,
                    'host': host
                }),
                success: function (response) {

                    adminInfoRequest(endpoint, title)
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            var msg = 'Both fields are required';
            MessageManager.showAlertError('Error', msg);
        }

    };
    // Add marketplace
    paintForm = function paintForm(endpoint, title) {

        $('#admin-container').empty();

        $.template('formTemplate', $('#form_template'));
        $.tmpl('formTemplate', {'title': title}).appendTo('#admin-container');

        $('#back').click(function () {
            $('#message-container').empty();
            if (main) {
                paintElementTable();
            } else {
                adminInfoRequest(endpoint, title);
            }
            main = false;
        });

        $('#request-button').click(function () {
            makeCreateRequest(endpoint, title);
        });
    };

    // Repaint initial table
    paintElementTable = function paintElementTable () {
        $('#admin-container').empty();
        $.template('adminElemTemplate', $('#admin_elem_template')); // Create the template
        $.tmpl('adminElemTemplate').appendTo("#admin-container"); // Render and append the template

        $('.show-markets').click(function() {
            adminInfoRequest('MARKET_COLLECTION', 'Marketplaces');
        });

        $('.show-rep').click(function() {
            adminInfoRequest('REPOSITORY_COLLECTION', 'Repositories');
        });

        $('.show-rss').click(function() {
            adminInfoRequest('RSS_COLLECTION', 'RSS');
        });

        $('.show-org').click(function() {
            orgInfoRequest(paintOrganizations);
        });

        $('.show-prof').click(function() {
            userInfoRequest();
        });

        $('.show-units').click(function() {
           unitsInfoRequest();
        });

        $('.add-market').click(function() {
            main = true;
            paintForm('MARKET_COLLECTION', 'Marketplace');
        });

        $('.add-rep').click(function() {
            main = true;
            paintForm('REPOSITORY_COLLECTION', 'Repository');
        });

        $('.add-rss').click(function() {
            main = true;
            paintForm('RSS_COLLECTION', 'RSS');
        });

        $('.add-org').click(function() {
            paintOrganizationForm();
        });

        $('.add-prof').click(function() {
            paintUserForm();
        });

        $('.add-unit').click(function() {
            paintUnitForm();
        });
    };

    refreshView = function refreshView() {
        paintElementTable();
    };

    setFooter = function setFooter() {
        // Append the terms and conditions bar
        // Check if the bar is included
        if ($('footer').length > 0) {
            $('footer').remove();
        }
        // Create the new footer
        $.template('footerTemplate', $('#footer_template'));
        $.tmpl('footerTemplate').appendTo('body');
        $('footer').css('position', 'absolute').css('top', ($(document).height() - 30) + 'px');
    }

    calculatePositions = function calculatePositions() {
        // Check window width
        if ($(window).width() < 981) {
            // Change headers position to avoid problems with bootstrap responsive
            // FIX ME: This positions are valid if the FI-LAB bar is included
            $('.title_wrapper').css('top', '-30px');
            $('.navigation').css('top', '-109px');
        } else {
            $('.title_wrapper').css('top', '140px');
            $('.navigation').css('top', '60px');
        }
        setFooter();
    }
    $(window).resize(calculatePositions);
})()
