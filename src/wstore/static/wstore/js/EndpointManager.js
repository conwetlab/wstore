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

    EndpointManager = {};

    // Contains endpoints that do not depend on variables 
    var staticEndpoints = {
        'MARKET_COLLECTION': '/api/administration/marketplaces',
        'REPOSITORY_COLLECTION': '/api/administration/repositories',
        'RSS_COLLECTION': '/api/administration/rss',
        'USERPROFILE_COLLECTION': '/api/administration/profiles',
        'ORGANIZATION_COLLECTION': '/api/administration/organizations',
        'RESOURCE_COLLECTION': '/api/offering/resources',
        'OFFERING_COLLECTION': '/api/offering/offerings',
        'APPLICATION_COLLECTION': '/api/offering/applications',
        'PURCHASE_COLLECTION': '/api/contracting',
        'NEWEST_COLLECTION': '/api/offering/offerings/newest',
        'TOPRATED_COLLECTION': '/api/offering/offerings/toprated',
        'UNIT_COLLECTION': '/api/administration/units',
        'CURRENCY_COLLECTION': '/api/administration/currency',
        'CHANGE_ORGANIZATION': '/api/administration/organizations/change',
        'REQUEST_PROVIDER': '/api/provider'
    };

    // Contains endpoints that depend on variables
    var contextEndpoints = {
        'MARKET_ENTRY': '/api/administration/marketplaces/${name}',
        'REPOSITORY_ENTRY': '/api/administration/repositories/${name}',
        'RSS_ENTRY': '/api/administration/rss/${name}',
        'USERPROFILE_ENTRY': '/api/administration/profiles/${username}',
        'ORGANIZATION_ENTRY': '/api/administration/organizations/${org}',
        'ORGANIZATION_USER_ENTRY': '/api/administration/organizations/${org}/users',
        'OFFERING_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}',
        'PUBLISH_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/publish',
        'TAG_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/tag',
        'BIND_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/bind',
        'REVIEW_COLLECTION': '/api/offering/offerings/${organization}/${name}/${version}/review',
        'REVIEW_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/review/${review}',
        'RESPONSE_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/review/${review}/response',
        'USDL_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/usdl',
        'SEARCH_ENTRY': '/api/search/keyword/${text}',
        'SEARCH_TAG_ENTRY': '/api/search/tag/${text}',
        'SEARCH_RESOURCE_ENTRY': '/api/search/resource/${org}/${name}/${version}',
        'CURRENCY_ENTRY': '/api/administration/currency/${currency}',
        'PURCHASE_ENTRY':   '/api/contracting/${ref}'
    };

    var clientStaticEndpoints = {
        'OFFERING_COLLECTION': '/search'
    };

    var clientContextEndpoints = {
        'SEARCH_ENTRY': '/search/keyword/${text}',
        'SEARCH_TAG_ENTRY': '/search/tag/${text}',
        'SEARCH_RESOURCE_ENTRY': '/search/resource/${org}/${name}/${version}',
        'OFFERING_ENTRY': '/offering/${organization}/${name}/${version}'
    };

    var selectEndpoint = function selectEndpoint(staticEP, contextEP, endpoint, options) {
        var result;

        if (endpoint in staticEP) {
            result = staticEP[endpoint];
        } else if (endpoint in contextEP) {
            $.template('endpointTemplate', contextEP[endpoint])
            result = $.tmpl('endpointTemplate', options).text();
        }

        return result;
    };

    /**
     * Returns the endpoint in string format rendered if necessary
     */
    EndpointManager.getEndpoint = function getEndpoint(endpoint, options) {
        return selectEndpoint(staticEndpoints, contextEndpoints, endpoint, options);
    }

    EndpointManager.getClientEndpoint = function getClientEndpoint(endpoint, options) {
        return selectEndpoint(clientStaticEndpoints, clientContextEndpoints, endpoint, options);
    }
})();
