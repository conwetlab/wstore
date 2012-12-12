
(function () {

	OfferingElement = function OfferingElement (offeringData) {
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
            this.shortDescription = offeringData.offering_description.shortDescription;
            this.updated = offeringData.offering_description.lastModified;
            this.created = offeringData.offering_description.created;
            this.description = offeringData.offering_description.longDescription;
            this.legal = offeringData.offering_description.legal;
            this.sla = offeringData.offering_description.sla;
            this.pricing = offeringData.offering_description.pricing;
            // Add the usdl information
        }

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

        OfferingElement.prototype.getDescription = function getDescription () {
            return this.description;
        };

        OfferingElement.prototype.getLegal = function getLegal () {
            return this.legal;
        };

        OfferingElement.prototype.getSla = function getSla () {
            return this.sla;
        };

        OfferingElement.prototype.getPricing = function getPricing () {
            return this.pricing;
        };
})();
