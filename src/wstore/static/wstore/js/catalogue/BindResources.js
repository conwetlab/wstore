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

    /**
     * Constructor for the resources binding ModalForm
     * @param offeringElement Offering object used in requests
     * @param vOnly Indicates if the window is in view only mode
     * @returns {BindResourcesForm}
     */
    BindResourcesForm = function BindResourcesForm (offeringElement, vOnly, callerObj) {
        this.viewOnly = vOnly;
        this.offeringElem = offeringElement;
        this.caller = callerObj;
        
    };

    /**
     * BindResourcesForm is a subclass of ModalForm
     */
    BindResourcesForm.prototype = new ModalForm('User resources', '#bind_resources_template');

    BindResourcesForm.prototype.constructor = BindResourcesForm;

    /**
     * Gets the user resources
     */
    BindResourcesForm.prototype.getUserResources = function getUserResources (callback, open) {
        var qstring = '';

        if (open) {
            qstring = '?open=true';
        }
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('RESOURCE_COLLECTION') + qstring,
            dataType: 'json',
            success: function (response) {
                callback(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    /**
     * Makes the resource binding request
     * @param resources: Resources to be bound
     */
    BindResourcesForm.prototype.bindResources = function bindResources () {
        var resSelected = [];
        for (var i = 0; i < this.resources.length; i++) {
            if ($('#check-' + i).prop("checked")) {
                resSelected.push({
                    'name': this.resources[i].name,
                    'version': this.resources[i].version
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
                'organization': this.offeringElem.getOrganization(),
                'name': this.offeringElem.getName(),
                'version': this.offeringElem.getVersion()
            }),
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(resSelected),
            success: (function (response) {
                MessageManager.showMessage('Bound', 'The resources have been bound');
                this.caller.refreshAndUpdateDetailsView();
            }).bind(this),
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    /**
     * Implements the method defined in ModalForm
     */
    BindResourcesForm.prototype.includeContents = function includeContents() {
        this.getUserResources(this.paintResources.bind(this));
    };

    /**
     * Paints the resources
     * @param resources Resources to be painted
     */
    BindResourcesForm.prototype.paintResources = function paintResources (resources) {
        this.resources = resources;

        // Append the provider resources
        for (var i = 0; i < resources.length; i++) {
            var res = resources[i];
            var found = false;
            var templ, j = 0;

            res.number = i;
            $.template('resourceTemplate', $('#resource_template'));
            templ = $.tmpl('resourceTemplate', res).
                appendTo('#resources');

            if (!this.viewOnly) {
                // Checks if the resource is already bound to the offering
                offeringRes = this.offeringElem.getResources()
                while(!found && j < offeringRes.length) {
                    if (res.name == offeringRes[j].name && res.version == offeringRes[j].version) {
                        found = true;
                        $('#check-' + i).prop('checked', true);
                    }
                    j++;
                }
            } else {
                // In the visualization mode it should be possible to expand resource info
                templ.click(function (self, resource) {
                    var resDetails = new ResourceDetailsPainter(resource, self);
                    return function () {
                        resDetails.paint();
                    }
                }(this, res));
            }
        }
        $('.modal-body').on('scroll', function() {
            $('.resource').popover('hide');
            $('.resource').removeClass('res-hover');
        })

        if(!this.viewOnly) {
            // Set listener
            $('.modal-footer > .btn').click((function () {
                this.bindResources();
            }).bind(this));
        } else {
            $('[type="checkbox"]').remove();
        }
    };

})();

(function() {

    ResourceDetailsPainter = function ResourceDetailsPainter(resource, caller) {
        this.resource = resource;
        this.caller = caller;
    };

    ResourceDetailsPainter.prototype.setListeners = function setListeners () {
        // Set back listener
        $('#res-back').click(function() {
            this.caller.display();
        }.bind(this));

        // TODO
        // Set delete listener
        // Set update listener
    };

    ResourceDetailsPainter.prototype.paint = function paint() {
        // Clean modal body
        $('.modal-body').empty()

        $.template('resourceDetails', $('#resource_details_template'));
        $.tmpl('resourceDetails', this.resource).appendTo('.modal-body');

        this.setListeners();
    };
})();