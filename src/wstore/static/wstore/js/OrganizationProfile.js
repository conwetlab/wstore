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

    OrganizationProfile = function OrganizationProfile() {
    };

    OrganizationProfile.prototype.buildProfile = function buildProfile(orgInfo) {
        this.name = orgInfo.name;

        this.notificationUrl = orgInfo.notification_url;

        if (orgInfo.tax_address) {
            this.taxAddress = orgInfo.tax_address;
        } else {
            this.taxAddress = null;
        }

        if (orgInfo.payment_info) {
            this.paymentInfo = orgInfo.payment_info;
        } else {
            this.paymentInfo = null;
        }

        this.limits = orgInfo.limits;

        this.manager = orgInfo.is_manager;

        // Notify the views that the organization profile is created
        refreshView();
    };

    OrganizationProfile.prototype.getUsername = function getUsername() {  // FIXME: change method name
        return this.name;
    };

    OrganizationProfile.prototype.getTaxAddress = function getTaxAddress() {
        return this.taxAddress;
    };

    OrganizationProfile.prototype.getPaymentInfo = function getPaymentInfo() {
        return this.paymentInfo;
    };

    OrganizationProfile.prototype.getNotificationUrl = function getNotificationUrl() {
        return this.notificationUrl;
    };

    OrganizationProfile.prototype.getExpenditureInfo = function getExpenditureInfo() {
        return this.limits;
    };

    OrganizationProfile.prototype.isManager = function isManager() {
        return this.manager;
    };

    OrganizationProfile.prototype.updateProfile = function updateProfile(orgInfo, callback, errorCallback) {
        var csrfToken = $.cookie('csrftoken');

        // Make PUT request
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: 'PUT',
            url: EndpointManager.getEndpoint('ORGANIZATION_ENTRY', {'org': this.name}),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(orgInfo),
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
    OrganizationProfile.prototype.fillUserInfo = function fillUserInfo(callback) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('ORGANIZATION_ENTRY', {'org': USERPROFILE.getCurrentOrganization()}),
            dataType: "json",
            success: (function (response) {
                this.buildProfile(response);
                if (callback) {
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