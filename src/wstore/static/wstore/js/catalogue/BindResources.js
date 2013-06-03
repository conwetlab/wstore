(function() {

    var offeringElem;

    var getUserResources = function getUserResources (callback, viewOnly) {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('RESOURCE_COLLECTION'),
            dataType: 'json',
            success: function (response) {
                callback(response, viewOnly);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var bindResources = function bindResources (resources) {
        var resSelected = [];
        for (var i = 0; i < resources.length; i++) {
            if ($('#check-' + i).prop("checked")) {
                resSelected.push({
                    'name': resources[i].name,
                    'version': resources[i].version
                })
            }
        }
        var csrfToken = $.cookie('csrftoken');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "POST",
            url: EndpointManager.getEndpoint('BIND_ENTRY', {
                'organization': offeringElem.getOrganization(),
                'name': offeringElem.getName(),
                'version': offeringElem.getVersion()
            }),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(resSelected),
            success: function (response) {
                MessageManager.showMessage('Binded', 'The resources have been binded');
                refreshAndUpdateDetailsView();
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var paintResources = function paintResources (resources, viewOnly) {
        MessageManager.showMessage('User resources', '');
        // Create the form
        $.template('bindResourcesTemplate', $('#bind_resources_template'));
        $.tmpl('bindResourcesTemplate' , {}).appendTo('.modal-body');

        // Apend the provider resources
        for (var i = 0; i < resources.length; i++) {
            var res = resources[i];
            var found = false;
            var j = 0;

            res.number = i;
            $.template('resourceTemplate', $('#resource_template'));
            $.tmpl('resourceTemplate', res).appendTo('#resources').on('hover', function(e) {
                $(e.target).popover('show');
            });

            if (!viewOnly) {
                // Checks if the resource is already binded to the offering
                offeringRes = offeringElem.getResources()
                while(!found && j < offeringRes.length) {
                    if (res.name == offeringRes[j].name && res.version == offeringRes[j].version) {
                        found = true;
                        $('#check-' + i).prop('checked', true);
                    }
                    j++;
                }
            }
        }

        if(!viewOnly) {
            // Set listener
            $('.modal-footer > .btn').click(function () {
                bindResources(resources);
            });
        } else {
            $('[type="checkbox"]').remove();
        }
    };

    bindResourcesForm = function bindResourcesForm (offeringElement, vOnly) {
        var viewOnly = false;
        if (vOnly) {
            viewOnly = true;
        }
        offeringElem = offeringElement;
        getUserResources(paintResources, viewOnly);
    };

})();
