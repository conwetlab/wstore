
(function () {

    var getRepositories = function getRepositories(callback) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('REPOSITORY_COLLECTION'),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr) {
                var msg = 'Error the server responds with code ' + xhr.status;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    paintCatalogue = function paintCatalogue() {
        // Get the catalogue template
        $.template('catalogueTemplate', $('#catalogue_search_template'));
        $.tmpl('catalogueTemplate', {}).appendTo('#catalogue-container');

        if ($('#create-app').length > 0) {
            $('#create-app').click(function () {
                getRepositories(showCreateAppForm);
            });
            $('#register-res').click(showRegisterResourceForm);
        }

        // Load data into the tabs on show
        $('a[data-toggle="tab"]').on('shown', function (e) {
            getUserOfferings(e.target.hash) // activated tab
        })

        // Load initial data
        getUserOfferings('#purchased-tab');
    };

    $(document).ready(paintCatalogue);
})();
