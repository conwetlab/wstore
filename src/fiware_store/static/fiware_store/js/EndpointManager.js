
(function () {

    EndpointManager = {};

    // Contains endpoints that do not depend on variables 
    var staticEndpoints = {
        'MARKET_COLLECTION': '/api/administration/marketplaces',
        'REPOSITORY_COLLECTION': '/api/administration/repositories',
        'RESOURCE_COLLECTION': '/api/offering/resources',
        'OFFERING_COLLECTION': '/api/offering/offerings',
        'PURCHASE_COLLECTION': '/api/contracting'
    };

    // Contains endpoints that depend on variables
    var contextEndpoints = {
        'MARKET_ENTRY': '/api/administration/marketplaces/${name}',
        'REPOSITORY_ENTRY': '/api/administration/repositories/${name}',
        'OFFERING_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}',
        'PUBLISH_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/publish',
        'BIND_ENTRY': '/api/offering/offerings/${organization}/${name}/${version}/bind',
        'SEARCH_ENTRY': '/api/search/${text}'
    }

    /**
     * Returns the endpoint in string format rendered if necesary
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
