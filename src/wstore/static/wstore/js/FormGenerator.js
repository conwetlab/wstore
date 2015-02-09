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

    FormGenerator = function FormGenerator () {
    }

    /*
     *
     */
    var generateControlGroup = function generateControlGroup (label, input) {
        var controlInput;
        var controlGroupTemplate = '<div class="control-group">';
        controlGroupTemplate += '<label class="control-label">${label}</label>';
        controlGroupTemplate += '<div class="controls">';
        controlGroupTemplate += '</div>';
        controlGroupTemplate += '</div>';

        if (input.mandatory) {
            label += '*';
        }

        $.template('cntrlGroupTemplate', controlGroupTemplate);
        controlInput = $.tmpl('cntrlGroupTemplate', {'label': label});

        controlInput.find('.controls').append(input);

        return controlInput;
    };

    /*
     *
     */
    var generateTextInput = function generateTextInput (name, inputInfo) {
        // Build text input structure
        var inputTemplate = '<input type="text" name="${name}" placeholder="${placeholder}" value="${val}"></input>';

        $.template('inputTemplate', inputTemplate);
        var input = $.tmpl('inputTemplate',  {
            'name': name,
            'placeholder': inputInfo.placeholder,
            'val': inputInfo.default 
        });

        // Return a control group with the input
        return generateControlGroup(inputInfo.label, input);
    };

    /*
     *
     */
    var generateSelectInput = function generateSelectInput (name, inputInfo) {
        // Build select structure
        var selectTemplate = '<select name="${name}" value="${val}"></select>';

        $.template('selectTemplate', selectTemplate);
        var selectInput = $.tmpl('selectTemplate', {
            'name': name,
            'val': inputInfo.default
        });

        // Append options
        for (var i = 0; i < inputInfo.options.length; i++) {
            var option = inputInfo.options[i];
            var optionInput = $('<option value="' + option.value + '">' + option.text + '</option>');

            selectInput.append(optionInput);
        }

        // Return a control group with the input
        return generateControlGroup(inputInfo.label, selectInput);
    };

    /*
     *
     */
    var genrateCheckboxInput = function genrateCheckboxInput (name, inputInfo) {
        // Build checkbox structure
        var checkboxTemplate = '<input type="checkbox" name="${name}" checked=${val}></input>${text}';

        $.template('checkboxTemplate', checkboxTemplate);
        var checkboxInput = $.tmpl('checkboxTemplate', {
            'name': name,
            'val': inputInfo.default,
        });

        // Return a control group with the input
        return generateControlGroup(inputInfo.label, checkboxInput);
    };

    /*
     *
     */
    var generateTextAreaInput = function generateTextAreaInput (name, inputInfo) {
        // Build textarea structure
        var textareaTemplate = '<textarea name="${name}" placeholder="${placeholder}">${val}</textarea>';

        $.template('textareaTemplate', textareaTemplate);
        var textareaInput = $.tmpl('textareaTemplate', {
            'name': name,
            'placeholder': inputInfo.placeholder,
            'val': inputInfo.default
        });

        // Return a control group with the input
        return generateControlGroup(inputInfo.label, textareaInput);
    };

    /*
     *
     */
    FormGenerator.prototype.generateForm = function generateForm (formInfo) {
        var form = $('<form class="form"><div id="error-container"></div></form>')
        var section = $('<section class="span10"></section>');

        var methods = {
            "text": generateTextInput,
            "textarea": generateTextAreaInput,
            "select": generateSelectInput,
            "checkbox": genrateCheckboxInput
        }

        // Iterate form fields
        for (var key in formInfo) {

            if (formInfo.hasOwnProperty(key)) {
                var input = methods[formInfo[key].type](key, formInfo[key])
                section.append(input);
            }
        }

        form.append(section);
        return form;
    };

 })();