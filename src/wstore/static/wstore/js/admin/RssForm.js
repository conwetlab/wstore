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

    RssForm = function RssForm() {
        // Build currency client
        this.currencyClient = new ServerClient('CURRENCY_ENTRY', 'CURRENCY_COLLECTION');
    };

    /**
     * RSS form is a subclass of AdminForm
     */
    RssForm.prototype = new AdminForm('RSS_ENTRY', 'RSS_COLLECTION', $('#rss_form_template'));
    RssForm.prototype.constructor = RssForm;

    /**
     * Implementation of the abstract method validateFields,
     * validate RSS creation form.
     */
    RssForm.prototype.validateFields = function validateFields() {
        var validation = {};
        var name, endpoint;

        validation.valid = true;

        // Check manadatory fields
        name = $.trim($('#rss-name').val());
        endpoint = $.trim($('#rss-endpoint').val());

        // Check the name
        if (!name) {
            validation.valid = false;
            validation.msg = 'Missing required field';
            validation.errFields = [$('#rss-name').parent().parent()];
        } else {
            var nameReg = new RegExp(/^[\w\s-]+$/);
            if (!nameReg.test(name)) {
                validation.valid = false;
                validation.msg = 'Invalid name format';
                validation.errFields = [$('#rss-name').parent().parent()];
            }
        }

        // Check the endpoint
        if (!endpoint) {
            if (validation.valid) {
                validation.valid = false;
                validation.msg = 'Missing required field';
                validation.errFields = [$('#rss-endpoint').parent().parent()];
            } else {
                validation.errFields.push($('#rss-endpoint').parent().parent());
            }
        } else {
            var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
            if (!urlReg.test(endpoint)) {
                if (!validation.valid) {
                    // Change validation message to indicate that more that an error exists
                    validation.msg += ' and invalid URL format';
                    validation.errFields.push($('#rss-endpoint').parent().parent());
                } else {
                    validation.valid = false;
                    validation.msg = 'Invalid URL format';
                    validation.errFields = [$('#rss-endpoint').parent().parent()];
                }
                
            }
        }

        // Get form info
        if (validation.valid) {
            var i, expenditureSet = false;
            var expTypes = ['perTransaction', 'weekly', 'monthly', 'daily'];
            var invalid = false;

            validation.data = {
                'name': name,
                'host': endpoint
            }
 
            // Check expenditure limits
            i = 0;
            while(i < expTypes.length && !invalid) {
                if ($.trim($('#' + expTypes[i]).val())) {
                    var exp = $.trim($('#'  + expTypes[i]).val());
                    expenditureSet = true;

                    // Check that a number has been included
                    if (!$.isNumeric(exp)) {
                        if (validation.valid) {
                            validation.valid = false;
                            validation.msg = 'Invalid expenditure limit';
                            validation.errFields = [$('#perTransaction').parent().parent()];
                        } else {
                            validation.msg += ' and invalid expenditure limit';
                            validation.errFields.push($('#perTransaction').parent().parent());
                        }
                        invalid = true;
                    } else {
                        var key = expTypes[i];
                        if (!validation.data.limits) {
                            validation.data.limits = {};
                        }
                        validation.data.limits[key] = exp;
                    }
                }
                i++;
            }
            // Include currency
            if (expenditureSet && validation.valid) {
                validation.data.limits.currency = $('#currency').val();
            }
            
        }
        // Get default models
        if (validation.valid) {
            var i = 0;
            var models = ['single-payment', 'subscription', 'use'];
            var invalid = false;
            var filled = 0;

            while (i < models.length && !invalid) {
                // Check if the field has been filled
                if ($.trim($('#' + models[i]).val())) {
                    var percent = $.trim($('#' + models[i]).val());

                    if (!$.isNumeric(percent) || ($.isNumeric(percent) && (parseFloat(percent) > 100 || parseFloat(percent) < 0))) {
                        if (validation.valid) {
                            validation.valid = false;
                            validation.msg = 'Invalid revenue model: Models must be a number between 0 and 100';
                            validation.errFields = [$('#' + models[i]).parent().parent()];
                        } else {
                            validation.msg += ' and invalid revenue model: Models must be a number between 0 and 100';
                            validation.errFields = [$('#' + models[i]).parent().parent()];
                        }
                    } else {
                        if (!validation.data.models) {
                            validation.data.models = [];
                        }
                        validation.data.models.push({
                            'class': models[i],
                            'percentage': percent
                        });
                    }
                    // Increment the number of filled fields
                    filled++;
                }
                i++;
            }
            if (filled > 0 && filled != 3) {
                if (validation.valid) {
                    validation.valid = false;
                    validation.msg = 'All the revenue models are required';
                    validation.errFields = [$('#use').parent().parent()];
                } else {
                    validation.msg += ' and all the revenue models are required';
                    validation.errFields = [$('#use').parent().parent()];
                }
            }
        }
        return validation;
    };

    /**
     * Display the RSS form and fill the RSS entry info for updating
     */
    RssForm.prototype.fillRSSInfo = function fillRSSInfo(rss) {
        var limits;

        // Paint the form
        this.paintForm();

        // Fill RSS entry info
        $('#rss-name').val(rss.name);
        $('#rss-endpoint').val(rss.host).prop('disabled', true);

        // Fill limits
        limits = rss.limits;
        if (limits.perTransaction) {
            $('#perTransaction').val(limits.perTransaction);
        }
        if (limits.weekly) {
            $('#weekly').val(limits.weekly);
        }
        if (limits.daily) {
            $('#daily').val(limits.daily);
        }
        if (limits.monthly) {
            $('#monthly').val(limits.monthly);
        }
        // Change register button by an update button
        $('#elem-submit').val('Update').unbind('click').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.updateElementRequest({'name': rss.name});
        }).bind(this));
    };

    /**
     * Implementation of the abstract method fillListinfo,
     * Include the list of registered RSS.
     */
    RssForm.prototype.fillListInfo = function fillListInfo(rss) {
        // Create the template
        $.template('elementTemplate', $('#element_template'));

        // Append RSSs
        for (var i = 0; i < rss.length; i++) {
            var editIcon;

            var template = $.tmpl('elementTemplate', {
                'name': rss[i].name,
                'host': rss[i].host
            });

            // Include edit icon
            editIcon = $('<i></i>').addClass('icon-edit').click((function(self, rssEntry) {
                return function() {
                    self.fillRSSInfo(rssEntry);
                };
            })(this, rss[i]));

            template.find('#elem-info').after(editIcon);

            // Include delete listener
            template.find('.delete').click((function(self, rssEntry) {
                return function() {
                    var urlContext = {
                        'name': rssEntry.name
                    }
                    self.mainClient.remove(self.elementInfoRequest.bind(self), urlContext);
                };
            })(this, rss[i]));
            
            // Append entry
            template.appendTo('#table-list');
        }
    };

    /**
     * Fill the allowed currencies in the
     * currency select input.
     */
    RssForm.prototype.currencyHandler = function currencyHandler(currencies) {
        var def;
        // Create currency select
        for (var i = 0; i < currencies.length; i++) {
            $('<option></option>').text(currencies[i].currency).attr('value', currencies[i].currency).appendTo('#currency');
            if (currencies[i]['default']) {
                def = currencies[i].currency;
            }
        }
        // Set default value
        $('#currency').val(def);
    };

    /**
     * Implementation of the abstract method setFormListeners,
     */
    RssForm.prototype.setFormListeners = function setFormListeners() {
        // Get available currencies
        this.currencyClient.get(this.currencyHandler.bind(this), {});
    };

})();