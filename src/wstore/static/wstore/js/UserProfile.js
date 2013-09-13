(function() {

    UserProfile = function UserProfile(userInfo) {
    };

    UserProfile.prototype.buildProfile = function buildProfile(userInfo) {
        this.username = userInfo.username;
        this.completeName = userInfo.complete_name;

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

        // Notify the views that the userprofile is created
        refreshView();
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

    UserProfile.prototype.updateProfile = function updateProfile(userInfo, callback) {
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