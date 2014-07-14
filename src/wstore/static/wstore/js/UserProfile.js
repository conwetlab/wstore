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

    UserProfile = function UserProfile() {
        this.firstLoad = true;
    };

    UserProfile.prototype.buildProfile = function buildProfile(userInfo) {
        this.username = userInfo.username;
        this.completeName = userInfo.complete_name;

        this.notificationUrl = userInfo.notification_url;

        if (userInfo.tax_address) {
            this.taxAddress = userInfo.tax_address;
        } else {
            this.taxAddress = null;
        }

        if (userInfo.payment_info) {
            this.paymentInfo = userInfo.payment_info;
        } else {
            this.paymentInfo = null;
        }

        this.roles = userInfo.roles;
        this.organizations = userInfo.organizations;
        this.currentOrganization = userInfo.current_organization;

        if (userInfo.provider_request) {
            this.providerRequest = userInfo.provider_request;
        } else {
            this.providerRequest = false;
        }

        this.expenditureLimits = userInfo.limits;
        // Notify the views that the userprofile is created
        if (!this.firstLoad) {
            refreshView();
        }
        this.firstLoad = false;
    }

    UserProfile.prototype.getUsername = function getUsername() {
        return this.username;
    };

    UserProfile.prototype.getCompleteName = function getCompleteName() {
        return this.completeName;
    };

    UserProfile.prototype.getCurrentOrganization = function getCurrentOrganization() {
        return this.currentOrganization;
    };

    UserProfile.prototype.getOrganizations = function getOrganizations() {
        return this.organizations;
    };

    UserProfile.prototype.getTaxAddress = function getTaxAddress() {
        return this.taxAddress;
    };

    UserProfile.prototype.getPaymentInfo = function getPaymentInfo() {
        return this.paymentInfo;
    };

    UserProfile.prototype.getUserRoles = function getUserRoles() {
        return this.roles;
    };

    UserProfile.prototype.providerRequested = function providerRequested() {
        return this.providerRequest;
    };

    UserProfile.prototype.getNotificationUrl = function getNotificationUrl() {
        return this.notificationUrl;
    };

    UserProfile.prototype.getExpenditureInfo = function getExpenditureInfo() {
        return this.expenditureLimits;
    };

    UserProfile.prototype.orgOwnerMember = function orgOwnerMember(offering) {
        return this.currentOrganization == offering.getOrganization();
    };

    UserProfile.prototype.isOwner = function isOwner(offering) {
        return (this.orgOwnerMember(offering)) &&
        ((this.username == offering.getProvider()) || ORGANIZATIONPROFILE.isManager());
    };

    UserProfile.prototype.getCurrentRoles = function getCurrentRoles() {
        var orgRoles;

        for (var i = 0; i < this.organizations.length; i++) {
            // Get roles for the current organization
            if (this.organizations[i].name == this.currentOrganization) {
                orgRoles = this.organizations[i].roles;
            }
        }
        return orgRoles;
    };

    UserProfile.prototype.changeOrganization = function changeOrganization(organization, callback) {
        var csrfToken = $.cookie('csrftoken');
        var request = {
            'organization': organization
        }

        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: 'PUT',
            url: EndpointManager.getEndpoint('CHANGE_ORGANIZATION'),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(request),
            success: (function (response) {
                // Update user info
                ORGANIZATION = organization;
                this.fillUserInfo(callback);
                refreshView();
            }).bind(this),
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                $('#message').modal('hide');
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    UserProfile.prototype.updateProfile = function updateProfile(userInfo, callback, errorCallback) {
        var csrfToken = $.cookie('csrftoken');

        // Make PUT request
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: 'PUT',
            url: EndpointManager.getEndpoint('USERPROFILE_ENTRY', {'username': this.username}),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(userInfo),
            success: (function (response) {
                // Update user info
                this.fillUserInfo(callback);
            }).bind(this),
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                errorCallback();
                $('#message').modal('hide');
                MessageManager.showMessage('Error', msg);
            }
        });
    }

    /**
     * This method is used to request user info and creates a
     * UserProfile object
     */
    UserProfile.prototype.fillUserInfo = function fillUserInfo(callback) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('USERPROFILE_ENTRY', {'username': USERNAME}),
            dataType: "json",
            success: (function (response) {
                this.buildProfile(response);
                // Create the organization profile if needed
                if (USERPROFILE.getCurrentOrganization() != USERPROFILE.getUsername()) {
                    ORGANIZATIONPROFILE = new OrganizationProfile();
                    if (callback) {
                        ORGANIZATIONPROFILE.fillUserInfo(callback);
                    } else {
                        ORGANIZATIONPROFILE.fillUserInfo(includeFilabOrgMenu);
                    }
                } else if(callback) {
                    callback();
                }
            }).bind(this),
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };
})();