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

    /**
     * Constructor for the Offering details view
     * @param offeringElement Offering to be displayed
     * @param backAction Function that specifies the action to be performed when the back button is pressed
     * @param container Container where the view is loaded
     * @returns {CatalogueDetailsView}
     */
    CatalogueDetailsView = function CatalogueDetailsView(offeringElement, backAction, container) {
        this.offeringElement = offeringElement;
        this.backAction = backAction;
        this.container = container;
        this.legalLoaded = false;
        this.pricingLoaded = false;
        this.slaLoaded = false;
        this.interLoaded = false;
        this.resLoaded = false;
        this.appLoaded = false;
    }

    /**
     * Displays the Catalogue Details view
     */
    CatalogueDetailsView.prototype.showView = function showView () {
        var screen, action, actions;

        // Clean the container
        $(this.container).empty();

        if (USERPROFILE.isOwner(this.offeringElement)) {
            actions = {
                'uploaded': 'Publish',
                'published': 'Delete',
                'purchased': null,
                'rated': null,
                'deleted': null
            };
        } else {
           actions = {
                'uploaded': null,
                'published': 'Purchase',
                'purchased': 'Download',
                'rated': 'Download',
                'deleted': null
            };
        }

        action = actions[this.offeringElement.getState()];

        if (action == 'Purchase' && USERPROFILE.orgOwnerMember(this.offeringElement)) {
            action = null;
        }
        
        $.template('detailsTemplate', $('#details_offering_template'));
        $.tmpl('detailsTemplate', {
            'name': this.offeringElement.getName(),
            'logo': this.offeringElement.getLogo(),
            'organization': this.offeringElement.getOrganization(),
            'owner': this.offeringElement.getProvider(),
            'version': this.offeringElement.getVersion(),
            'updated': this.offeringElement.getPublication(),
            'action': action
        }).appendTo(this.container);

        if (action == null) {
            $('#main-action').remove();
        }
        // Check price for action button
        if (action == 'Purchase') {
            var priceStr = getPriceStr(this.offeringElement.getPricing());
            if (priceStr != 'View pricing'){
                $('#main-action').val(priceStr);
                if (priceStr == 'Free') {
                    $('#main-action').removeClass('btn-blue');
                    $('#main-action').addClass('btn-success');
                }
            }
        }
        fillStarsRating(this.offeringElement.getRating(), $('#details-stars'));

        // Load the main info template
        $.template('mainInfoTemplate', $('#main_info_offering_template'));
        $.tmpl('mainInfoTemplate', {
            'description': this.offeringElement.getDescription()
        }).appendTo('#main-tab');

        // Check if there are screenshots
        screen = this.offeringElement.getScreenshots();
        if (screen.length > 0) {
            for (var i = 0; i < screen.length; i++) {
                var imageDiv = $('<div></div>').addClass('item');
                imageDiv.append($('<img src="' + screen[i] +'" alt />'));

                if (i == 0) {
                    imageDiv.addClass('active');
                }
                imageDiv.appendTo('.carousel-inner');
            };
        } else {
            $('h2:contains(Screenshots)').remove();
            $('#screenshots-car').remove();
        }

        // Check tags
        if (!this.offeringElement.getTags().length && !USERPROFILE.isOwner(this.offeringElement)) {
            $('h2:contains(Tags)').addClass('hidden');
            $('#main-tab .icon-tags').addClass('hidden');

        } else if (this.offeringElement.getTags()) {
            // Write tags
            var tags = this.offeringElement.getTags();
            var tagElem = $('#tags');
            for (var i = 0; i < tags.length; i++) {
                var icn = $('<i></i>').addClass('icon-tag');
                var cont = $('<code></code>').append(icn);

                // Add search by tag listener if needed
                if ('StoreSearchView' in window) {
                    var tagLink = $('<a></a>').addClass('tag').text(tags[i]).appendTo(cont);
                    tagLink.click(function() {
                        var searchView = new StoreSearchView('SEARCH_TAG_ENTRY');
                        $('#home-container').empty();
                        searchView.setTitle($(this).text());
                        searchView.initSearchView('SEARCH_TAG_ENTRY', $(this).text());
                    });
                } else {
                    var tagLink = $('<span></span>').addClass('tag').text(tags[i]).appendTo(cont);
                }
                tagElem.prepend(cont);
            }
            var clear = $('<div></div>').addClass('space clear');
            $('#tags').prepend(clear);
        }

        // Include the update Tags button if needed
        if (USERPROFILE.isOwner(this.offeringElement)) {

            var updateBtn = $('<code></code>').attr('id', 'update-tags').click((function() {
                var tagManager = new TagManager(this.offeringElement, this);
                tagManager.display();
            }).bind(this));
            updateBtn.append('<i class="icon-plus"></i>');
            $('#tags').append(updateBtn);

            // Set advanced operations
            // Delete offering
            if(this.offeringElement.getState() != 'deleted') {

                $('<li><a>Delete offering</a></li>').appendTo('#advanced-op').click((function() {
                    var msg = "Are you sure that you want to delete the offering";
                    MessageManager.showYesNoWindow(msg, (function() {
                        this.deleteOffering();
                    }).bind(this), 'Delete');
                }).bind(this));
            }

            // Bind resources and edit the offering
            if (this.offeringElement.getState() == 'uploaded') {
                $('<li><a>Bind resources</a></li>').appendTo('#advanced-op').click((function() {
                    var resForm = new BindResourcesForm(this.offeringElement, false, this);
                    resForm.display();
                }).bind(this));
                $('<li><a>Edit</a></li>').appendTo('#advanced-op').click((function() {
                    editOfferingForm(this.offeringElement, this);
                }).bind(this));
            }
        }
        // Download service model
        $('<li><a>Download service model</a></li>').appendTo('#advanced-op').click((function() {
            this.getServiceModel();
        }).bind(this));

        // Set the main operation
        $('#main-action').click((function() {
            this.mainAction(action);
        }).bind(this));

        this.buildTabs();

        $('#back').click((function (e) {
            $(this.container).empty();
            this.backAction();
        }).bind(this));

        //Check renovations
        if (action == 'Download') {
            this.checkRenovations();
        }

        // Calculate positions on resize
        this.calculatePositions();
        $(window).resize(this.calculatePositions.bind(this));

        // Form for comment and rate the offering
        //if (this.offeringElement.getComments().length) {
            this.reviewPainter = new ReviewPainter(this.offeringElement, $('#review-container'), this);
            this.reviewPainter.paint();
        //}
        closeMenuPainter();
    };

    /**
     * Set all displayed components in the correct place depending on the window
     * size
     */
    CatalogueDetailsView.prototype.calculatePositions = function calculatePositions() {
        var position = $('.tabbable').offset();
        // Fixed position in: Details and Catalogue Tab
        var offset;
        var width;

        // Calculate tabs width
        $('.detailed-info').css('width', ($(window).width() - position.left) + 'px');

        offset = $(window).height() - $('.tab-content').offset().top - 30;
        width = $(window).width() - $('.tab-content').offset().left -10;
        $('.tab-content').css('height', offset.toString() + 'px');
        $('.tab-content').css('width', width.toString() + 'px');

        if ('reviewPainter' in this) {
            this.reviewPainter.checkExpand();
        }
    };

    /**
     * Check if the user needs to renovate a subscription in this offering
     */
    CatalogueDetailsView.prototype.checkRenovations = function checkRenovations() {
        var price_plans = this.offeringElement.getPricing().price_plans;
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
                paintRenovationForm(outDated, offElem, this);
            }
        }
    };

    /**
     * Performs the main action of the details view
     * @param action Action to be performed
     */
    CatalogueDetailsView.prototype.mainAction = function mainAction (action) {
        if (action == 'Publish') {
            publishOffering(this.offeringElement, this);
        } else if (action == 'Purchase'){
            purchaseOffering(this.offeringElement, this);
        } else if (action == 'Delete') {
            var msg = "Are you sure that you want to delete the offering";
            MessageManager.showYesNoWindow(msg, (function() {
                this.deleteOffering();
            }).bind(this));
        } else if (action == 'Download') {
            downloadElements(this.offeringElement);
        }
    };

    /**
     * Deletes the offering
     */
    CatalogueDetailsView.prototype.deleteOffering = function deleteOffering () {
        var csrfToken = $.cookie('csrftoken');
        $.ajax({
            headers: {
                'X-CSRFToken': csrfToken,
            },
            type: "DELETE",
            url: EndpointManager.getEndpoint('OFFERING_ENTRY', {
            'organization': this.offeringElement.getOrganization(),
            'name': this.offeringElement.getName(),
            'version': this.offeringElement.getVersion()
            }),
            dataType: 'json',
            success: (function (response) {
                MessageManager.showMessage('Deleted', 'The offering has been deleted');
                $(this.container).empty();
                this.backAction();
            }).bind(this),
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        });
    };

    /**
     * Downloads the service model of the offering
     */
    CatalogueDetailsView.prototype.getServiceModel = function getServiceModel () {
        window.open(EndpointManager.getEndpoint('USDL_ENTRY', {
            'organization': this.offeringElement.getOrganization(),
            'name': this.offeringElement.getName(),
            'version': this.offeringElement.getVersion()
        }));
    };

    var setTab = function setTab(self, tabId, text, painter) {
     // Include the tab
        var li = $('<li></li>');
        $('<a></a>').text(text).attr('href', '#' + tabId).attr('data-toggle', 'tab').appendTo(li);
        $('<div></div>').addClass('tab-pane').attr('id', tabId).appendTo('.tab-content');
        $('.nav-tabs').append(li);
        // Set the listener
        $('a[href="#'+ tabId +'"]').on('shown', (function (e) {
            painter();
        }).bind(self));
    }
    /**
     * Builds the tabs whose in has been provided in the offering
     */
    CatalogueDetailsView.prototype.buildTabs = function buildTabs() {
        // Check which tabs to include
        // Interactions
        if (this.offeringElement.getInteractions().length > 0) {
            setTab(this, 'int-tab', 'Interactions', this.paintInteractionProtocols.bind(this));
        }

        // Legal conditions
        if (this.offeringElement.getLegal().length > 0) {
            setTab(this, 'legal-tab', 'Legal', this.paintLegal.bind(this));
        }

        // Pricing
        if (this.offeringElement.getPricing().price_plans.length > 0) {
            setTab(this, 'pricing-tab', 'Pricing', this.paintPricing.bind(this));
        }

        // Service level agreement
        if (this.offeringElement.getSla().length > 0) {
            setTab(this, 'sla-tab', 'Service Level Agreement', this.paintSla.bind(this));
        }

        // Resources
        if (this.offeringElement.getResources().length > 0) {
            setTab(this, 'res-tab', 'Resources', this.paintResources.bind(this));
        }

        // Applications
        if (this.offeringElement.getApplications().length > 0) {
            setTab(this, 'app-tab', 'Applications', this.paintApplications.bind(this));
        }
    };

    CatalogueDetailsView.prototype.paintLegalClauses = function paintLegalClauses (clauses, dom) {
        if (clauses.length > 0) {
            $('<h3></h3>').text('Clauses').appendTo('.clauses');
            $.template('legalClausesTemplate', $('#legal_clauses_template'));
            $.tmpl('legalClausesTemplate', clauses).appendTo(dom);
        }
    };

    CatalogueDetailsView.prototype.paintLegal = function paintLegal () {
        if (!this.legalLoaded) {
            var legal = this.offeringElement.getLegal();

            this.legalLoaded = true;
            // Create the tab for legal conditions
            $('<h2></h2>').text('Legal conditions').appendTo('#legal-tab');
            $.template('legalTemplate', $('#legal_template'));

            for (var i = 0; i < legal.length; i++) {
                var dom;

                dom = $.tmpl('legalTemplate', {
                    'name': legal[i].name,
                    'description': legal[i].description
                })
                dom.appendTo('#legal-tab');
                if('clauses' in legal[i]) {
                    this.paintLegalClauses(legal[i].clauses, dom.find('.clauses'));
                }
            }
        }
    };

    CatalogueDetailsView.prototype.paintPriceElement = function paintPriceElement (priceElem, dom, type) {
        if (priceElem.length > 0) {
            var priceTempl;

            title = null;
            if (type == 'taxes') {
                title = 'Taxes';
            } else if (type == 'components') {
                title = 'Price components';
            }
            $('<h3></h3>').text(title).appendTo(dom);

            for (var i = 0; i < priceElem.length; i++) {
                // Check if a price function has been defined
                if (!priceElem.text_function) {
                    $.template('priceElementTemplate', $('#pricing_element_template'));
                    priceTempl = $.tmpl('priceElementTemplate', priceElem[i]);

                    if(priceElem[i].renovation_date) {
                        $('<p></p>').text(priceElem[i].renovation_date).appendTo(priceTempl);
                    }

                } else {
                    $.template('priceElementTemplate', $('#pricing_function_template'));
                    priceTempl = $.tmpl('priceElementTemplate', priceElem[i]);
                }
                priceTempl.appendTo(dom)
            }
        }
    };

    CatalogueDetailsView.prototype.paintPricing = function paintPricing () {
        if (!this.pricingLoaded) {
            var price_plans = this.offeringElement.getPricing().price_plans;

            this.pricingLoaded = true;

            $('<h2></h2>').text('Pricing Information').appendTo('#pricing-tab');

            $.template('pricingTemplate', $('#pricing_template'));

            for (var i = 0; i < price_plans.length; i++) {
                var dom;
                dom = $.tmpl('pricingTemplate', {
                    'title': price_plans[i].title,
                    'description': price_plans[i].description
                });
                dom.appendTo('#pricing-tab');
                if ('price_components' in price_plans[i]) {
                    this.paintPriceElement(price_plans[i].price_components, dom.find('.price-components'), 'components');
                }

                if ('taxes' in price_plans[i]) {
                    this.paintPriceElement(price_plans[i].taxes, dom.find('.taxes'), 'taxes');
                }
                // Paint a line for separating plans if needed
                if (i != (price_plans.length - 1)) {
                    $('<div></div>').addClass('line clear').appendTo(dom);
                }
            }
        }
    };

    CatalogueDetailsView.prototype.paintSlaVariables =  function paintSlaVariables (variables, dom) {
        if(variables.length > 0) {
            $('<h5></h5>').text('Variables').appendTo(dom);
            $.template('slaVariableTemplate', $('#sla_variable_template'));
            $.tmpl('slaVariableTemplate', variables).appendTo(dom);
        }
    };

    CatalogueDetailsView.prototype.paintSlaExpresions = function paintSlaExpresions (expresions, dom) {
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
                    this.paintSlaVariables(expresions[i].variables, varDom.find('.variables'));
                }
                varDom.appendTo(dom);
            };
        }
    };

    CatalogueDetailsView.prototype.paintSla = function paintSla () {
        if(!this.slaLoaded) {
            var sla = this.offeringElement.getSla();

            this.slaLoaded = true;
            $('<h2></h2>').text('Service level agreement information').appendTo('#sla-tab');

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
                    this.paintSlaExpresions(sla[i].slaExpresions, dom.find('.expresions'));
                }
            };
        }
    };

    CatalogueDetailsView.prototype.paintInteractionParams = function paintInteractionParams (params, domElem, title) {
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

    CatalogueDetailsView.prototype.paintInteractions = function paintInteractions (interactions, domElem) {
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
                this.paintInteractionParams(interactions[i].inputs, inter.find('.inputs'), 'Inputs');
            }

            if ('outputs' in interactions[i] && interactions[i].outputs.length > 0) {
                this.paintInteractionParams(interactions[i].outputs, inter.find('.outputs'), 'Outputs');
            }
        }
    };

    CatalogueDetailsView.prototype.paintInteractionProtocols = function paintInteractionProtocols () {
        if(!this.interLoaded) {
            var interactions = this.offeringElement.getInteractions();

            this.interLoaded = true;
            $('<h2></h2>').text('Interaction protocols information').appendTo('#int-tab');

            $.template('intProtTemplate', $('#int_prot_template'));

            for (var i = 0; i < interactions.length; i++) {
                var prot = $.tmpl('intProtTemplate', {
                    'title': interactions[i].title,
                    'description': interactions[i].description,
                    'technical_interface': interactions[i].technical_interface
                });
                prot.appendTo('#int-tab');

                if ('interactions' in interactions[i] && interactions[i].interactions.length > 0) {
                    this.paintInteractions(interactions[i].interactions, prot.find('.interactions'));
                }
            }
        }
    };

    CatalogueDetailsView.prototype.paintResources = function paintResources () {
        if(!this.resLoaded) {
            var resources = this.offeringElement.getResources();

            this.resLoaded = true;
            $('<h2></h2>').text('Offering resources').appendTo('#res-tab');
            for (var i = 0; i < resources.length; i++) {
                var cont = $('<div></div>');
                var p;
                var b;
                p = $('<p></p>').appendTo(cont);
                b = $('<b>Name: </b>').addClass('color-interactions');
                p.append(b);
                p.append(resources[i].name);

                p = $('<p></p>').appendTo(cont);
                b = $('<b>Version: </b>').addClass('color-interactions');
                p.append(b);
                p.append(resources[i].version);

                p = $('<p></p>').appendTo(cont);
                b = $('<b>Description: </b>').addClass('color-interactions');
                p.append(b);
                p.append(resources[i].description);

                cont.append('<div class="space clear"></div>');

                cont.appendTo('#res-tab');
            }
        }
    };

    CatalogueDetailsView.prototype.paintApplications = function paintApplications () {
        if(!this.appLoaded) {
            var applications = this.offeringElement.getApplications();

            this.appLoaded = true;
            $('<h2></h2>').text('Applications').appendTo('#app-tab');
            for (var i = 0; i < applications.length; i++) {
                var cont = $('<div></div>');
                var p;
                var b;
                p = $('<p></p>').appendTo(cont);
                b = $('<b>Name: </b>').addClass('color-interactions');
                p.append(b);
                p.append(applications[i].name);

                p = $('<p></p>').appendTo(cont);
                b = $('<b>URL: </b>').addClass('color-interactions');
                p.append(b);
                p.append(applications[i].url);

                p = $('<p></p>').appendTo(cont);
                b = $('<b>Description: </b>').addClass('color-interactions');
                p.append(b);
                p.append(applications[i].description);

                cont.append('<div class="space clear"></div>');

                cont.appendTo('#app-tab');
            }
        }
    };

    CatalogueDetailsView.prototype.refreshAndUpdateDetailsView = function refreshAndUpdateDetailsView () {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('OFFERING_ENTRY', {
                'organization': this.offeringElement.getOrganization(),
                'name': this.offeringElement.getName(),
                'version': this.offeringElement.getVersion()
            }),
            dataType: 'json',
            success: (function (response) {
                var newElem = new OfferingElement(response)
                this.update(newElem);
            }).bind(this),
            error: function (xhr) {
            }
        });
    };

    CatalogueDetailsView.prototype.update = function update (offElement) {
        this.offeringElement = offElement;
        this.legalLoaded = false;
        this.pricingLoaded = false;
        this.slaLoaded = false;
        this.interLoaded = false;
        this.resLoaded = false;
        this.appLoaded = false;
        this.showView();
    };

})();
