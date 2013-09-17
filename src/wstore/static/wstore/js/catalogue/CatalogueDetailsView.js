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

(function  () {

    var offElem;
    var backAct;
    var detContainer;
    var legalLoaded;
    var pricingLoaded;
    var slaLoaded;
    var interLoaded;
    var resLoaded;
    var appLoaded

    paintOfferingDetails = function paintOfferingDetails (offeringElement, backAction, container) {
        var screen, action;

        offElem = offeringElement;
        backAct = backAction;
        detContainer = container;
        legalLoaded = false;
        pricingLoaded = false;
        slaLoaded = false;
        interLoaded = false;
        resLoaded = false;
        appLoaded = false
        // Create the details view

        // Clean the container
        $(container).empty();

        // Load the main template
        if (offeringElement.getState() == 'uploaded') {
            action = 'Publish';
        } else if (offeringElement.getState() == 'published') {
            if ((USERNAME == offeringElement.getProvider()) && (ORGANIZATION == offeringElement.getOrganization())) {
                action = 'Delete';
            } else {
                action = 'Purchase';
            }
        } else if (offeringElement.getState() == 'purchased' || offeringElement.getState() == 'rated') {
            action = 'Download';
        } else {
            action = null;
        }

        $.template('detailsTemplate', $('#details_offering_template'));
        $.tmpl('detailsTemplate', {
            'name': offeringElement.getName(),
            'logo': offeringElement.getLogo(),
            'organization': offeringElement.getOrganization(),
            'owner': offeringElement.getProvider(),
            'version': offeringElement.getVersion(),
            'updated': offeringElement.getPublication(),
            'action': action
        }).appendTo(container);

        if (action == null) {
            $('#main-action').remove();
        }
        fillStarsRating(offeringElement.getRating(), $('#details-stars'));

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

        if (offeringElement.getState() != 'uploaded') {
            paintComments();
        } else {
            $('h3:contains(Comments)').addClass('hide');
        }

        // Set listeners
        $('a[href="#int-tab"]').on('shown', function (e) {
            paintInteractionProtocols(offeringElement.getInteractions());
        });

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

        $('a[href="#app-tab"]').on('shown', function (e) {
            paintApplications(offeringElement.getApplications());
        });

        $('#back').click(function (e) {
            $(container).empty();
            backAction();
        });

        // Set advanced operations
        if((USERNAME == offeringElement.getProvider()) && 
          (ORGANIZATION == offeringElement.getOrganization()) &&
          (offeringElement.getState() != 'deleted')) {

            $('<input></input>').attr('type', 'button').attr('value', 'Delete offering').addClass('btn btn-danger btn-advanced').appendTo('#advanced-op').click(function() {
                var msg = "Are you sure that you want to delete the offering";
                MessageManager.showYesNoWindow(msg, function() {
                    deleteOffering(offeringElement, backAction, container);
                });
            });
        }

        $('<input></input>').attr('type', 'button').attr('value', 'Download service model').addClass('btn btn-advanced').appendTo('#advanced-op').click(function() {
            getServiceModel(offeringElement);
        });

        if((USERNAME == offeringElement.getProvider()) && 
          (ORGANIZATION == offeringElement.getOrganization()) && 
          (offeringElement.getState() == 'uploaded')) {
            $('<input></input>').attr('type', 'button').attr('value', 'Bind resources').addClass('btn btn-advanced').appendTo('#advanced-op').click(function() {
                var resForm = new BindResourcesForm(offeringElement);
                resForm.display();
            });
            $('<input></input>').attr('type', 'button').attr('value', 'Edit').addClass('btn btn-advanced').appendTo('#advanced-op').click(function() {
                editOfferingForm(offeringElement);
            });
        }

        // Set the main operation
        $('#main-action').click(mainAction.bind(this, action));

        //Check renovations
        if (action == 'Download') {
            checkRenovations(offeringElement.getPricing());
        }

        if (offeringElement.getState() == 'purchased') {
            $('#comment-btn').removeClass('hide').click(function() {
                paintCommentForm(offeringElement);
            });
        }
    };

    var paintComments = function paintComments() {
        var comments = offElem.getComments();

        for (var i = 0; i < comments.length; i++) {
            var templ;

            $.template('commentTemplate', $('#comment_template'));
            templ = $.tmpl('commentTemplate', {
                'user': comments[i].user,
                'timestamp': comments[i].timestamp.split(' ')[0],
                'title': comments[i].title,
                'comment': comments[i].comment
            });

            fillStarsRating(comments[i].rating, templ.find('.comment-rating'));
            templ.appendTo('#comments');
        }
    }
    var checkRenovations = function checkRenovations(pricing) {
        var price_plans = pricing.price_plans;
        if (price_plans.length > 0) {
            var outDated = [];
            var toRenovate = false;
            // Check if there are renovation dates
            for (var i = 0; i < price_plans.length; i++) {
                var price_components;

                if (price_plans[i].price_components) {
                    price_components = price_plans[i].price_components;

                    for (var j = 0; j < price_components.length; j++) {
                        // Check if there are out of date subscriptions
                        if ('renovation_date' in price_components[j]) {
                            var currentDate = new Date();
                            var renDate = new Date(price_components[j].renovation_date);

                            if (renDate.getTime() < currentDate.getTime()) {
                                if (!toRenovate) {
                                    toRenovate = true;
                                }
                                outDated.push(price_components[j]);
                            }
                        }
                    }
                }
            }
            // If out of date subscriptions show renovation window
            if (toRenovate) {
                paintRenovationForm(outDated, offElem);
            }
        }
    };

    var mainAction = function mainAction (action) {
        if (action == 'Publish') {
            publishOffering(offElem);
        } else if (action == 'Purchase'){
            purchaseOffering(offElem);
        } else if (action == 'Delete') {
            var msg = "Are you sure that you want to delete the offering";
            MessageManager.showYesNoWindow(msg, function() {
                deleteOffering(offElem, backAct, detContainer);
            });
        } else if (action == 'Download') {
            downloadElements(offElem);
        }
    };

    var deleteOffering = function deleteOffering (offeringElement, backAction, container) {
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
                $(container).empty();
                backAction();
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
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
        if (priceElem.length > 0) {
            var priceTempl;

            title = null;
            if (type == 'taxes') {
                title = 'Taxes';
            } else if (type == 'components') {
                title = 'Price components';
            }
            $('<h4></h4>').text(title).appendTo(dom);

            for (var i = 0; i < priceElem.length; i++) {
                $.template('priceElementTemplate', $('#pricing_element_template'));
                priceTempl = $.tmpl('priceElementTemplate', priceElem[i]);

                if(priceElem[i].renovation_date) {
                    $('<p></p>').text(priceElem[i].renovation_date).appendTo(priceTempl);
                }
                priceTempl.appendTo(dom)	
            }
        }
    };

    var paintPricing = function paintPricing (pricing) {
        if (!pricingLoaded) {
            var price_plans = pricing.price_plans;

            pricingLoaded = true;

            $('<h2></h2>').text('Pricing Infomation').appendTo('#pricing-tab');

            if (price_plans.length > 0){
                $.template('pricingTemplate', $('#pricing_template'));

                for (var i = 0; i < price_plans.length; i++) {
                    var dom;
                    dom = $.tmpl('pricingTemplate', {
                        'title': price_plans[i].title,
                        'description': price_plans[i].description
                    });
                    dom.appendTo('#pricing-tab');
                    if ('price_components' in price_plans[i]) {
                        paintPriceElement(price_plans[i].price_components, dom.find('.price-components'), 'components');
                    }

                    if ('taxes' in price_plans[i]) {
                        paintPriceElement(price_plans[i].taxes, dom.find('.taxes'), 'taxes');
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
                    dom.appendTo('#sla-tab');
                    if('slaExpresions' in sla[i]){
                        paintSlaExpresions(sla[i].slaExpresions, dom.find('.expresions'));
                    }
                };
            } else {
                $('<p></p>').text('No service level agreement has been defined').appendTo('#sla-tab');
            }
        }
    };

    var paintInteractionParams = function paintInteractionParams (params, domElem, title) {
        $('<h4></h4>').text(title).appendTo(domElem);
        $.template('intParamTemplate', $('#int_param_template'));

        for (var i = 0; i < params.length; i++) {
            $.tmpl('intParamTemplate', {
                'label': params[i].label,
                'description': params[i].description,
                'interface_element': params[i].interface_element
            }).appendTo(domElem);
        }
    };

    var paintInteractions = function paintInteractions (interactions, domElem) {
        $('<h3></h3>').text('Interactions').appendTo(domElem);
        $.template('interactTemplate', $('#int_template'));

        for (var i = 0; i < interactions.length; i++) {
            var inter = $.tmpl('interactTemplate', {
                'title': interactions[i].title,
                'description': interactions[i].description,
                'interface_operation': interactions[i].interface_operation
            });
            inter.appendTo(domElem);
            if ('inputs' in interactions[i] && interactions[i].inputs.length > 0) {
                paintInteractionParams(interactions[i].inputs, inter.find('.inputs'), 'Inputs');
            }

            if ('outputs' in interactions[i] && interactions[i].outputs.length > 0) {
                paintInteractionParams(interactions[i].outputs, inter.find('.outputs'), 'Outputs');
            }
        }
    };

    var paintInteractionProtocols = function paintInteractionProtocols (interactions) {
        if(!interLoaded) {
            interLoaded = true;
            $('<h2></h2>').text('Interaction protocols information').appendTo('#int-tab');

            if(interactions.length > 0) {
                $.template('intProtTemplate', $('#int_prot_template'));

                for (var i = 0; i < interactions.length; i++) {
                    var prot = $.tmpl('intProtTemplate', {
                        'title': interactions[i].title,
                        'description': interactions[i].description,
                        'technical_interface': interactions[i].technical_interface
                    });
                    prot.appendTo('#int-tab');

                    if ('interactions' in interactions[i] && interactions[i].interactions.length > 0) {
                        paintInteractions(interactions[i].interactions, prot.find('.interactions'));
                    }
                }
            } else {
                $('<p></p>').text('No interaction protocols have been defined').appendTo('#int-tab');
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

    var paintApplications = function paintApplications (applications) {
        if(!appLoaded) {
            appLoaded = true;
            $('<h2></h2>').text('Applications').appendTo('#app-tab');
            if (applications.length > 0) {
                for (var i = 0; i < applications.length; i++) {
                    var cont = $('<div></div>');
                    var p;
                    p = $('<p></p>').appendTo(cont);
                    p.append('<b>Name: </b>');
                    p.append(applications[i].name);

                    p = $('<p></p>').appendTo(cont);
                    p.append('<b>URL: </b>');
                    p.append(applications[i].url);

                    p = $('<p></p>').appendTo(cont);
                    p.append('<b>Description: </b>');
                    p.append(applications[i].description);

                    cont.appendTo('#app-tab');
                }
            } else {
                $('<p></p>').text('The offering has no applications').appendTo('#app-tab');
            }
        }
    };

    refreshAndUpdateDetailsView = function refreshAndUpdateDetailsView () {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('OFFERING_ENTRY', {
                'organization': offElem.getOrganization(),
                'name': offElem.getName(),
                'version': offElem.getVersion()
            }),
            dataType: 'json',
            success: function (response) {
                var newElem = new OfferingElement(response)
                paintOfferingDetails(newElem, backAct, detContainer);
            },
            error: function (xhr) {
            }
        });
    };

    refreshDetailsView = function refreshDetailsView (offeringElement) {
        paintOfferingDetails(offeringElement, backAct, detContainer);
    };
})();
