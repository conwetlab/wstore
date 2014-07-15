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

    Loader = function Loader() {
        this.pageManager = new PageManager();
        this.currentPage = this.pageManager.getPageLoader(INITIAL_PAGE);
    };

    /**
     * This method builds the menu used to change between organizations
     */
    Loader.prototype.includeFilabOrgMenu = function includeFilabOrgMenu() {
        var organizations = USERPROFILE.getOrganizations();
        $('.dropdown-submenu').remove();

        // Include switch session menu if the user belong to
        // any organization
        if (organizations.length > 1) {
            var ul, userElem;
            var leftMenu = $('<li></li>').addClass('dropdown-submenu pull-left');
            $('<a></a>').text('Switch session').appendTo(leftMenu);
            $('<i></i>').addClass('icon-caret-right').appendTo(leftMenu);

            ul = $('<ul></ul>').addClass('dropdown-menu dropdown-menu-header').appendTo(leftMenu);

            for (var i = 0; i < organizations.length; i++) {
                if (organizations[i].name != USERPROFILE.getCurrentOrganization()) {
                    var li = $('<li></li>');
                    var a = $('<a></a>').attr('data-placement','left').attr('data-toggle', 'tooltip');
                    var span = $('<span></span>').text(organizations[i].name).css('vertical-align', 'super').css('margin-left', '6px');
                    a.append(span);
                    a.appendTo(li);

                    if (organizations[i].name == USERPROFILE.getUsername()) {
                        span.text(USERPROFILE.getCompleteName());
                        a.prepend($('<img></img>').attr('src', '/static/oil/img/user.png').css('width', '20px'));
                        ul.prepend(li);
                    } else {
                        a.prepend($('<img></img>').attr('src', '/static/oil/img/group.png').css('width', '20px'));
                        ul.append(li);
                    }
                    // Set listeners for organizations switching
                    li.click((function(org) {
                        return function() {
                            USERPROFILE.changeOrganization(org, includeFilabOrgMenu);
                        }
                    })(organizations[i].name));
                }
            }

            // Load styles depending on the fi-lab bar
            if ($('#oil-bar').length) {
                ul.css('display', 'none');
                ul.css('position', 'absolute');
                ul.css('top', '10px');
                ul.css('right', '157px');
                userElem = $('#oil-usr');

            } else {
                leftMenu.css('width', '100%')
                ul.css('display', 'none');
                ul.css('position', 'absolute');
                ul.css('top', '0px');
                ul.css('left', '-158px');
                userElem = $('#user-name')
            }

            leftMenu.on('mouseover', function() {
                ul.css('display', 'block');
            });

            leftMenu.on('mouseout', function() {
                ul.css('display', 'none');
            });
            $('#settings-menu').prepend(leftMenu);

            if (USERPROFILE.getCurrentOrganization() == USERPROFILE.getUsername()) {
                $('.oil-usr-icon').attr('src', '/static/oil/img/user.png');
                userElem.text(USERPROFILE.getCompleteName());
            } else {
                $('.oil-usr-icon').attr('src', '/static/oil/img/group.png');
                userElem.text(USERPROFILE.getCurrentOrganization());
            }
            if (!$('#oil-bar').length && $.trim(userElem.text()).length > 12) {
                var shortName = userElem.text().substring(0, 9) + '...';
                userElem.text(shortName);
            }
        }
        if(!$('#oil-bar').length) {
            $('#settings-menu').css('right', '0');
            $('#settings-menu').css('left', 'initial');
        }
    };

    /**
     * Builds the current organization profile
     */
    Loader.prototype.checkOrg = function checkOrg() {
        ORGANIZATIONPROFILE = new OrganizationProfile();
        ORGANIZATIONPROFILE.fillUserInfo(this.includeFilabOrgMenu.bind(this));
    };

    Loader.prototype.setCurrentPage = function setCurrentPage(page) {
        this.currentPage = this.pageManager.getPageLoader(page);
    };

    Loader.prototype.loadPage = function loadPage() {
        this.currentPage();
    };

    Loader.prototype.readyHandler = function readyHandler() {
        var userForm;

        USERPROFILE = new UserProfile()
        USERPROFILE.fillUserInfo(this.checkOrg.bind(this));

        $('#conf-link').click(function() {
            var profile = USERPROFILE;
            var isOrg = false;

            if (USERPROFILE.getCurrentOrganization() != USERPROFILE.getUsername()) {
                profile = ORGANIZATIONPROFILE;
                isOrg = true;
            }
            userForm = new UserConfForm(profile, isOrg);
            userForm.display();
        });
    }
})();

var pageLoader = new Loader();

refreshView = function refreshView() {
    pageLoader.loadPage();
};

$(document).ready(pageLoader.readyHandler.bind(pageLoader));
