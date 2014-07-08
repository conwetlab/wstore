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

    OfferingElement = function OfferingElement (offeringData) {
        this.fillOfferingInfo(offeringData);
        // Add the usdl information
    }

    OfferingElement.prototype.fillOfferingInfo = function fillOfferingInfo(offeringData) {
        this.name = offeringData.name;
        this.organization = offeringData.owner_organization;
        this.provider = offeringData.owner_admin_user_id;
        this.version = offeringData.version;
        this.logo = offeringData.image_url;
        this.state = offeringData.state;
        this.resources = offeringData.resources;
        this.rating = offeringData.rating;
        this.comments = offeringData.comments;
        this.tags = offeringData.tags;
        this.screenshots = offeringData.related_images;

        this.servicesOffered = offeringData.offering_description.services_included;

        this.shortDescription = this.servicesOffered[0].short_description;
        this.updated = this.servicesOffered[0].modified;
        this.created = offeringData.creation_date;

        // Display only publication date (not hour or seconds)
        if (offeringData.publication_date) {
            this.published = offeringData.publication_date.substring(0, 10);
        }
        this.description = this.servicesOffered[0].long_description;
        this.offeringDescriptionURL = offeringData.description_url;
        this.legal = this.servicesOffered[0].legal;
        this.sla = this.servicesOffered[0].sla;
        this.interactions = this.servicesOffered[0].interactions;
        this.pricing = offeringData.offering_description.pricing;
        this.bill = [];
        this.open = offeringData.open;

        if (this.state == 'purchased' || this.state == 'rated') {
            this.bill = offeringData.bill;
        }
        if (offeringData.applications) {
            this.applications = offeringData.applications;
        } else {
            this.applications = [];
        }
    };

    OfferingElement.prototype.updateOfferingInfo = function updateOfferingInfo(callback) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('OFFERING_ENTRY', {
                'name': this.name,
                'organization': this.organization,
                'version': this.version
            }),
            dataType: 'json',
            success: (function(response) {
                this.fillOfferingInfo(response);
                if (callback) {
                    callback(this);
                }
            }).bind(this)
        });
    };

    OfferingElement.prototype.getId = function getId () {
        return this.organization + '__' + this.name + '__' + this.version;
    };

    OfferingElement.prototype.getName = function getName () {
        return this.name;
    };

    OfferingElement.prototype.getOrganization = function getOrganization () {
        return this.organization;
    };

    OfferingElement.prototype.getProvider = function getProvider () {
        return this.provider;
    };

    OfferingElement.prototype.getVersion = function getVersion () {
        return this.version;
    };

    OfferingElement.prototype.getLogo = function getLogo () {
        return this.logo;
    };

    OfferingElement.prototype.getState = function getState () {
        return this.state;
    };

    OfferingElement.prototype.getResources = function getResources () {
        return this.resources;
    };

    OfferingElement.prototype.getRating = function getRating () {
        return this.rating;
    };

    OfferingElement.prototype.getComments = function getComments () {
        return this.comments;
    };

    OfferingElement.prototype.getTags = function getTags () {
        return this.tags;
    };

    OfferingElement.prototype.getScreenshots = function getScreenshots () {
        return this.screenshots;
    };

    OfferingElement.prototype.getShortDescription = function getShortDescription () {
        return this.shortDescription;
    };

    OfferingElement.prototype.getUpdated = function getUpdated () {
        return this.updated;
    };

    OfferingElement.prototype.getCreated = function getCreated () {
        return this.created;
    };

    OfferingElement.prototype.getPublication = function getPublication () {
        return this.published;
    };

    OfferingElement.prototype.getDescription = function getDescription () {
        return this.description;
    };

    OfferingElement.prototype.getOfferingDescriptionURL = function getOfferingDescriptionURL () {
        return this.offeringDescriptionURL;
    };

    OfferingElement.prototype.getLegal = function getLegal () {
        return this.legal;
    };

    OfferingElement.prototype.getSla = function getSla () {
        return this.sla;
    };

    OfferingElement.prototype.getInteractions = function getInteractions () {
        return this.interactions;
    };

    OfferingElement.prototype.getPricing = function getPricing () {
        return this.pricing;
    };

    OfferingElement.prototype.getBillPath = function getBillPath () {
        return this.bill;
    };

    OfferingElement.prototype.getApplications = function getApplications() {
        return this.applications;
    };

    OfferingElement.prototype.setState = function setState (state) {
        this.state = state;
    };

    OfferingElement.prototype.isOpen = function isOpen() {
        return this.open;
    }
})();
