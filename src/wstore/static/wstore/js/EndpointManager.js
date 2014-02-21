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
        'ORGANIZATION_USER_ENTRY': '/api/administration/organizations/${org}/user',
        'OFFERING_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}',
        'PUBLISH_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/publish',
        'TAG_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/tag',
        'BIND_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/bind',
        'RATING_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/rating',
        'USDL_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/usdl',
        'SEARCH_ENTRY': '/api/search/${text}',
        'PURCHASE_ENTRY':   '/api/contracting/${ref}'
    }

    /**
     * Returns the endpoint in string format rendered if necessary
     */
    EndpointManager.getEndpoint = function getEndpoint(endpoint, options) {
        var result;

        if (endpoint in staticEndpoints) {
            result = staticEndpoints[endpoint];
        } else if (endpoint in contextEndpoints) {
            $.template('endpointTemplate', contextEndpoints[endpoint])
            result = $.tmpl('endpointTemplate', options).text();
        }

        return result;
    }
})();
