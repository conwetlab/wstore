/*
 * Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid
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

ComponentSlider = function ComponentSlider() {
    this.$list = $('.sliding-list');
    this.width = this.$list.width();
};

var showNext = function () {
    $('.sliding-list > :first-child').appendTo(this.$list);
    this.$list.css('left', '');
};

ComponentSlider.prototype.back = function back() {
    this.$list.animate({ left: + this.width }, 200, function () {
        $('.sliding-list > :last-child').prependTo(this.$list);
        this.$list.css('left', '');
    }.bind(this));
}

ComponentSlider.prototype.next = function next() {
    this.$list.animate({ left: - this.width }, 200, showNext.bind(this));
}

ComponentSlider.prototype.resize = function resize() {
    this.$list.css({
        width: $('.sliding-item').css('width', this.width).length * this.width,
        marginLeft: - this.width
    });
}

ComponentSlider.prototype.setElement = function setElement (value) {
    var found = false;
    var i = 0;

    while (!found && i < this.$list.children().length) {
        var currElement = this.$list.children().eq(1);

        if (currElement.find('.title').text() == value) {
            found = true;
        } else {
            var next = showNext.bind(this);
            next();
            i++;
        }
    }
};

ComponentSlider.prototype.init = function init() {
    $('.control-back').on('click', this.back.bind(this));
    $('.control-next').on('click', this.next.bind(this));
    this.resize();
    $('.sliding-list > :last-child').prependTo(this.$list);
}

})();

(function() {

    PricingEditor = function PricingEditor(container, units, currencies) {

        // Load template
        $.template('pricingTemplate', $('#pricing_form_template'));
        $.tmpl('pricingTemplate').appendTo(container);

        this.pricing = {
            'price_plans': []
        };

        this.existingPlans = [];

        this.currentComponents = [];

        // Parse units to divide group them in types
        this.units = {
            'single payment': [],
            'subscription': [],
            'pay per use': []
        }

        for (var i = 0; i < units.length; i++) {
            this.units[units[i].defined_model].push(units[i].name)
        }

        this.currencies = currencies;
    };

    var setErrorFields = function (msg, fields) {
        // Show the error message
        MessageManager.showAlertError('Error', msg, $('#error-message-pricing'));
        $('.alert-error').removeClass('span8');

        // Set error fields
        for (var i = 0; i < fields.length; i++) {
            var errField = fields[i];

            errField.parent().parent().addClass('error');

            errField.change(function() {
                $('#error-message-pricing').empty();
                $('.error').removeClass('error');
            })
        }
    };

    var getPlanIndex = function(self, plan) {
        var index = -1;
        var i = 0;
        var found = false;

        // Remove the plan
        while (!found && i < self.existingPlans.length) {
            if (plan == self.existingPlans[i]) {
                index = i;
                found = true;
            }
            i++;
        }
        return index;
    };

    var editHandler = function (evnt) {
        var planElem = $(evnt.target).parent();
        var index = getPlanIndex(this, planElem.text());

        var plan = this.pricing.price_plans[index];

        if ($('#pricing-label').length) {
            var msg = "Please save or remove your current price plan before editing";
            MessageManager.showAlertWarning('Warning', msg, $('#error-message-pricing'));
            return;
        }

        var addPlan = addPlanHandler.bind(this);
        addPlan();

        $('#pricing-label').val(plan.label);
        $('#pricing-title').val(plan.title);
        $('#pricing-description').val(plan.description);
        $('#pricing-currency').val(plan.currency);

        this.currentComponents = plan.price_components.slice(0);

        // Build price component boxes
        for (var i = 0; i < this.currentComponents.length; i++) {
            var cmpElem = $('<div class="plan-selected"><i class="icon-save"></i><i class="icon-remove"></i></div>').appendTo($('#comp-container'));
            buildEditBox(cmpElem, this.currentComponents[i].label, editCmp.bind(this), removeCmpHandler.bind(this));
        }

        this.existingPlans.splice(index, 1);
        this.pricing.price_plans.splice(index, 1);

        planElem.remove();
    };

    var removeHandler = function(evnt) {
        // search for the price plan
        var planElem = $(evnt.target).parent();
        var index = getPlanIndex(this, planElem.text());

        if (index > -1) {
            this.existingPlans.splice(index, 1);
            this.pricing.price_plans.splice(index, 1);
        }

        planElem.remove();
    };

    var savePlanHandler = function(evnt) {
        var label, title, description, msg;
        var errHandler = setErrorFields.bind(this);

        label = $.trim($('#pricing-label').val());
        title = $.trim($('#pricing-title').val());
        description = $.trim($('#pricing-description').val());

        if (!label || !title || !description) {
            msg = "Missing required field in Price Plan: ";
            var errFields = [];
            if (!label) {
                msg += ' Label';
                errFields.push($('#pricing-label'));
            }
            if (!title) {
                msg += ' Display name';
                errFields.push($('#pricing-title'));
            }
            if (!description) {
                msg += ' Description';
                errFields.push($('#pricing-description'));
            }

            errHandler(msg, errFields);
            return;
        }

        // Check if the selected plan has already been included
        if ($.inArray(label, this.existingPlans) > -1) {
            msg = "The price plan " + label + " has already been defined";
            MessageManager.showAlertError('Error', msg, $('#error-message-pricing'));
            errHandler(msg, [$('#pricing-label')]);
            return;
        }

        var components = this.currentComponents.slice(0);
        this.currentComponents = [];

        var pricePlan = {
            'label': label,
            'title': title,
            'description': description,
            'currency': $('#pricing-currency').val(),
            'price_components': components
        };

        buildEditBox($(evnt.target).parent(), label, editHandler.bind(this), removeHandler.bind(this));

        $('#add-price-plan').click(addPlanHandler.bind(this));
        $('#plan-form').removeAttr('style');
        $('#plan-form').empty();

        this.existingPlans.push(pricePlan.label);
        this.pricing.price_plans.push(pricePlan);
    };

    var getComponentIndex = function(label) {
        var index = -1;
        var i = 0, found = false;

        // Remove price component
        while (!found && i < this.currentComponents.length) {
            if (this.currentComponents[i].label == label) {
                found = true;
            } else {
                i++;
            }
        }

        if (found) {
            index = i;
        }

        return index;
    };

    var removeCmp = function(label) {
        var getIndex = getComponentIndex.bind(this);
        var i = getIndex(label);

        if (i > -1) {
            this.currentComponents.splice(i, 1);
        }
    };

    var removeCmpHandler = function(evnt) {
        var label = $(evnt.target).parent().text();
        var remover = removeCmp.bind(this);

        // Remove component slider
        $('#slider-container').empty();
        // Remove box
        $(evnt.target).parent().remove();

        remover(label);
    };

    var editCmp = function(evnt) {
        var loader = addComponentHandler.bind(this);
        var remover = removeCmp.bind(this);
        var label = $(evnt.target).parent().text();

        var getIndex = getComponentIndex.bind(this);
        var i = getIndex(label);

        loader(evnt);

        $('#comp-label').val(this.currentComponents[i].label);
        $('#comp-description').val(this.currentComponents[i].description);
        this.compSlider.setElement(this.currentComponents[i].unit);

        $('.sliding-list').children().eq(1).find('.editable-text').val(this.currentComponents[i].value);

        remover(label);
        $(evnt.target).parent().remove();
    };

    var savePriceComponent = function(evnt) {
        var error = false;
        var getIndex = getComponentIndex.bind(this);
        var errHandler = setErrorFields.bind(this);

        // Validate component info
        var label = $.trim($('#comp-label').val());
        var desc = $.trim($('#comp-description').val());
        var selectedCmp = $('.sliding-list').children().eq(1);
        var value = $.trim(selectedCmp.find('.editable-text').val())

        // Check that mandatory fields has been included
        if (!label || !desc) {
            var msg = "Missing required field in price component: ";
            var errFields = [];

            if (!label) {
                msg += ' label';
                errFields.push($('#comp-label'));
            }
            if (!desc) {
                msg += ' description';
                errFields.push($('#comp-description'))
            }

            errHandler(msg, errFields);
            return;
        }

        // Check that a valid value has been included
        if (!$.isNumeric(value)) {
            var msg = "The value provided for the price component must be a number";
            errHandler(msg, []);
            return;
        }

        // Check that the label is not already in use
        if (getIndex(label) > -1) {
            var msg = "The label " + label + " is already used";
            errHandler(msg, [$('#comp-label')]);
            return;
        }

        this.currentComponents.push({
            'label': label,
            'description': desc,
            'value': value,
            'unit': selectedCmp.find('.title').text()
        });

        buildEditBox($(evnt.target).parent(), label, editCmp.bind(this), removeCmpHandler.bind(this));

        $('#add-price-comp').click(addComponentHandler.bind(this));
        $('#slider-container').empty();
    };

    var buildEditBox = function(target, label, editHandler, removeHandler) {
        target.empty();
        target.text(label)
        target.append('<i class="icon-pencil"></i>');
        target.append('<i class="icon-remove"></i>');

        // Create listeners
        target.find('.icon-pencil').click(editHandler);
        target.find('.icon-remove').click(removeHandler);
    };

    var addSaveBox = function(container, saveHandlr, removeHandlr) {
        var planElem = $('<div class="plan-selected"><i class="icon-save"></i><i class="icon-remove"></i></div>').appendTo(container);
        planElem.find('.icon-save').click(saveHandlr);
        planElem.find('.icon-remove').click(removeHandlr);
    };

    var buildSliderContents = function(units, priceClass) {
        var slideElemTmpl = '<div class="sliding-item ' + priceClass + '">';
        slideElemTmpl += '<div class="price"><input type="text" class="editable-text" value="0.00"></span></div></div>';

        for (var i = 0; i < units.length; i++) {
            var unit = $('<div class="title">' +  units[i] + '</div>');
            var elemTmpl = $(slideElemTmpl);
            elemTmpl.append(unit);
            elemTmpl.appendTo('.sliding-list');
        }
    };

    var addComponentHandler = function(evnt) {
        // Disconect add button
        $('#add-price-comp').off();

        // Add component slider
        $.template('compTemplate', $('#control_slider_template'));
        $.tmpl('compTemplate').appendTo('#slider-container');

        buildSliderContents(this.units['subscription'], 'payment-subs');
        buildSliderContents(this.units['pay per use'], 'payment-usage');

        // Create component slider handlers
        this.compSlider = new ComponentSlider();
        this.compSlider.init();

        addSaveBox('#comp-container', savePriceComponent.bind(this), function(evnt) {
            var remover = removeCmpHandler.bind(this)
            remover(evnt);
            $('#add-price-comp').click(addComponentHandler.bind(this));
        }.bind(this));
    };

    var addPlanHandler = function(evnt) {
        $.template('planTemplate', $('#price_plan_form_template'));
        $.tmpl('planTemplate').appendTo($('#plan-form'));
        $('#plan-form').attr('style', 'height: 260px;');

        // Populate currency select
        var def;
        for (var i = 0; i < this.currencies.length; i++) {
            curr = this.currencies[i].currency;
            $('<option value="' + curr + '">' +  curr + '</option>').appendTo('#pricing-currency');

            if (this.currencies[i].default) {
                def = curr;
            }
        }
        $('#pricing-currency').val(def);
        $('#add-price-plan').off();

        addSaveBox('#price-plans', savePlanHandler.bind(this), function(evnt) {
            var remHdl = removeHandler.bind(this);
            remHdl(evnt);
            $('#add-price-plan').click(addPlanHandler.bind(this));
            $('#plan-form').removeAttr('style');
            $('#plan-form').empty();
        }.bind(this))

        // Include component hadler
        $('#add-price-comp').click(addComponentHandler.bind(this));
    };

    PricingEditor.prototype.createListeners = function createListeners() {
        $('#add-price-plan').click(addPlanHandler.bind(this));
    }

    PricingEditor.prototype.getPricing = function getPricing() {
        return this.pricing;
    }

})();