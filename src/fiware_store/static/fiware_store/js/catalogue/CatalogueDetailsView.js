(function  () {

    var legalLoaded;
    var pricingLoaded;
    var slaLoaded;
    var resLoaded;

    paintOfferingDetails = function paintOfferingDetails (offeringElement) {
        var screen, action;

        legalLoaded = false;
        pricingLoaded = false;
        slaLoaded = false;
        resLoaded = false;
        // Create the details view

        // Clean the container
        $('#catalogue-container').empty();

        // Load the main template
        if (offeringElement.getState() == 'uploaded') {
            action = 'Publish';
        } else if (offeringElement.getState() == 'published') {
            if (USERNAME == offeringElement.getProvider()) {
                action = 'Delete';
            } else {
                action = 'Purchase';
            }
        }

        $.template('detailsTemplate', $('#details_offering_template'));
        $.tmpl('detailsTemplate', {
            'name': offeringElement.getName(),
            'logo': offeringElement.getLogo(),
            'organization': offeringElement.getOrganization(),
            'owner': offeringElement.getProvider(),
            'version': offeringElement.getVersion(),
            'updated': offeringElement.getUpdated(),
            'action': action
        }).appendTo('#catalogue-container');

        // Load the main info template
        $.template('mainInfoTemplate', $('#main_info_offering_template'));
        $.tmpl('mainInfoTemplate', {
            'description': offeringElement.getDescription()
        }).appendTo('#main-tab');

        screen = offeringElement.getScreenshots();
        for (var i = 0; i < screen.length; i++) {
            var imageDiv = $('<div></div>').addClass('item');
            imageDiv.append($('<img src="' + screen[i] +'" alt />'));

            if (i == 0) {
                imageDiv.addClass('active');
            }
            imageDiv.appendTo('.carousel-inner');
        };

        // Set listeners
        $('a[href="#legal-tab"]').on('shown', function (e) {
            paintLegal(offeringElement.getLegal());
        });

        $('a[href="#pricing-tab"]').on('shown', function (e) {
            paintPricing(offeringElement.getPricing());
        });

        $('a[href="#sla-tab"]').on('shown', function (e) {
            paintSla(offeringElement.getSla());
        });

        $('a[href="#res-tab"]').on('shown', function (e) {
            paintResources(offeringElement.getResources());
        });

        $('#back').click(function (e) {
            $('#catalogue-container').empty();
            paintCatalogue();
        });

        // Set advanced operations
        if(USERNAME == offeringElement.getProvider()) {
            $('<input></input>').attr('type', 'button').attr('value', 'Delete offering').addClass('btn btn-danger btn-advanced').appendTo('#advanced-op').click(function() {
                var msg = "Are you sure that you want to delete the offering";
                MessageManager.showYesNoWindow(msg, function() {
                    deleteOffering(offeringElement);
                });
            });
        }
        $('<input></input>').attr('type', 'button').attr('value', 'Download service model').addClass('btn btn-advanced').appendTo('#advanced-op').click(function() {
            getServiceModel(offeringElement);
        });

        if(USERNAME == offeringElement.getProvider() && offeringElement.getState() == 'uploaded') {
            $('<input></input>').attr('type', 'button').attr('value', 'Bind resources').addClass('btn btn-advanced').appendTo('#advanced-op').click(function() {
                resLoaded = false;
                bindResourcesForm(offeringElement);
            });
        }

        // Set the main operation
        $('#main-action').click(mainAction.bind(this, action, offeringElement));
    };

    var mainAction = function mainAction (action, offeringElement) {
        if (action == 'Publish') {
            publishOffering(offeringElement);
        } else if (action == 'Purchase'){
            purchaseOffering(offeringElement);
        } else if (action == 'Delete') {
            deleteOffering(offeringElement);
        }
    };

    var deleteOffering = function deleteOffering (offeringElement) {
        var csrfToken = $.cookie('csrftoken');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "DELETE",
            url: EndpointManager.getEndpoint('OFFERING_ENTRY', {
            'organization': offeringElement.getOrganization(),
            'name': offeringElement.getName(),
            'version': offeringElement.getVersion()
            }),
            dataType: 'json',
            success: function (response) {
                MessageManager.showMessage('Deleted', 'The offering has been deleted');
                $('#catalogue-container').empty();
                paintCatalogue();
            },
            error: function (xhr) {
                var msg = 'Error: the server responds with code ' + xhr.status;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    var getServiceModel = function getServiceModel (offeringElement) {
        window.open(offeringElement.getOfferingDescriptionURL());
    };

    var paintLegalClauses = function paintLegalClauses (clauses, dom) {
        if (clauses.length > 0) {
            $('<h3></h3>').text('Clauses').appendTo('.clauses');
            $.template('legalClausesTemplate', $('#legal_clauses_template'));
            $.tmpl('legalClausesTemplate', clauses).appendTo(dom);
        }
    };

    var paintLegal = function paintLegal (legal) {
        if (!legalLoaded) {
            legalLoaded = true;

            $('<h2></h2>').text('Legal conditions').appendTo('#legal-tab');

            if (legal.length > 0) {
                $.template('legalTemplate', $('#legal_template'));

                for (var i = 0; i < legal.length; i++) {
                    var dom;

                    dom = $.tmpl('legalTemplate', {
                        'name': legal[i].name,
                        'description': legal[i].description
                    })
                    dom.appendTo('#legal-tab');
                    if('clauses' in legal[i]) {
                        paintLegalClauses(legal[i].clauses, dom.find('.clauses'));
                    }
                }
            } else {
                $('<p></p>').text('No legal conditions have been defined').appendTo('#legal-tab');
            }
        }
    };

    var paintPriceElement = function paintPriceElement (priceElem, dom, type) {
        if (priceElem > 0) {
            title = null;
            if (type == 'taxes') {
                title = 'Taxes';
            } else if (type == 'components') {
                title = 'Price components';
            }
            $('<h4></h4>').text(title).appendTo(dom);
            $.template('priceElementTemplate', $('#pricing_element_template'));
            $.tmpl('priceElementTemplate', priceElem).appendTo(dom);
        }
    };

    var paintPricing = function paintPricing (pricing) {
        if (!pricingLoaded) {
            pricingLoaded = true;

            $('<h2></h2>').text('Pricing Infomation').appendTo('#pricing-tab');

            if (pricing.length > 0){
                $.template('pricingTemplate', $('#pricing_template'));

                for (var i = 0; i < pricing.length; i++) {
                    var dom;
                    dom = $.tmpl('pricingTemplate', {
                        'title': pricing[i].title,
                        'description': pricing[i].description
                    });
                    dom.appendTo('#pricing-tab');
                    if ('priceComponents' in pricing[i]) {
                        paintPriceElement(pricing[i].priceComponents, dom.find('.price-components'), 'components');
                    }

                    if ('taxes' in pricing[i]) {
                        paintPriceElement(pricing[i].taxes, dom.find('.taxes'), 'taxes');
                    }
                }
            } else {
                $('<p></p>').text('No pricing information has been defined. This offering is free').appendTo('#pricing-tab');
            }
        }
    };

    var paintSlaVariables =  function paintSlaVariables (variables, dom) {
        if(variables.length > 0) {
            $('<h5></h5>').text('Variables').appendTo(dom);
            $.template('slaVariableTemplate', $('#sla_variable_template'));
            $.tmpl('slaVariableTemplate', variables).appendTo(dom);
        }
    };

    var paintSlaExpresions = function paintSlaExpresions (expresions, dom) {
        if(expresions.length > 0) {
            $('<h3></h3>').text('Service level expresions').appendTo(dom);
            $.template('slaExpresionsTemplate', $('#sla_expresion_template'));

            for (var i = 0; i < expresions.length; i++) {
                var varDom;
                varDom = $.tmpl('slaExpresionsTemplate', {
                    'title': expresions[i].name,
                    'description': expresions[i].description
                })

                if('location' in expresions[i] && 'variables' in expresions[i]){
                    expresions.variables.push({
                        'label': 'Centre',
                        'value': 'UTM X:' + expresions[i].location.coordinates.lat + ', UTM Y:' + expresions[i].location.coordinates.long,
                        'type': '',
                        'unit': ''
                    });
                }

                if('variables' in expresions[i]) {
                    paintSlaVariables(expresions[i].variables, varDom.find('.variables'));
                }
                varDom.appendTo(dom);
            };
        }
    };

    var paintSla = function paintSla (sla) {
        if(!slaLoaded) {
            slaLoaded = true;
            $('<h2></h2>').text('Service level agreement information').appendTo('#sla-tab');

            if (sla.length > 0) {
                $.template('slaTemplate', $('#sla_template'));

                for (var i = 0; i < sla.length; i++) {
                    var dom;
                    dom = $.tmpl('slaTemplate', {
                        'title': sla[i].title,
                        'description': sla[i].description,
                        'obligated': sla[i].obligatedParty.substring(sla[i].obligatedParty.indexOf('#') + 1)
                    });
                    dom.appendTo('sla-tab');
                    if('slaExpresions' in sla[i]){
                        paintSlaExpresions(sla[i].slaExpresions, dom.find('.expresions'));
                    }
                };
            } else {
                $('<p></p>').text('No service level agreement has been defined').appendTo('#sla-tab');
            }
        }
    };

    var paintResources = function paintResources (resources) {
        if(!resLoaded) {
            resLoaded = true;
            $('<h2></h2>').text('Offering resources').appendTo('#res-tab');
            if (resources.length > 0) {
            for (var i = 0; i < resources.length; i++) {
                var cont = $('<div></div>');
                var p;
                p = $('<p></p>').appendTo(cont);
                p.append('<b>Name: </b>');
                p.append(resources[i].name);

                p = $('<p></p>').appendTo(cont);
                p.append('<b>Version: </b>');
                p.append(resources[i].version);

                p = $('<p></p>').appendTo(cont);
                p.append('<b>Description: </b>');
                p.append(resources[i].description);

                cont.appendTo('#res-tab');
            }
            } else {
                $('<p></p>').text('The offering has no resources').appendTo('#res-tab');
            }
        }
    };

})();
