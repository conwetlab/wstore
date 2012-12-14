
(function () {

    EndpointManager = {};

    // Contains endpoints that do not depend on variables 
    var staticEndpoints = {
        'MARKET_COLLECTION': '/api/administration/marketplaces',
        'REPOSITORY_COLLECTION': '/api/administration/repositories',
        'RESOUCE_COLLECTION': '/api/offerings/resources',
        'APPLICATION_COLLECTION': '/api/offerings/applications'
    };

    // Contains endpoints that depend os variables
    var contextEndpoints = {
        'MARKET_ENTRY': '/api/administration/marketplaces/${name}',
        'REPOSITORY_ENTRY': '/api/administration/repositories/${name}',
        'APPLICATION_ENTRY': '/api/offerings/applications/${organization}/${name}/${version}'
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
