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
     * Admin forms constructor
     */
    AdminForm = function AdminForm(entry, collection, formTemplate) {
        this.main = true;
        this.mainClient = new ServerClient(entry, collection);
        this.formTemplate = formTemplate;
    };

    /**
     * Private method the manager the back action
     */
    var backHandler = function backHandler(self) {
        if (self.main) {
            paintElementTable();
        } else {
            self.elementInfoRequest();
        }
    };

    /**
     * Make the request for administration elements
     */
    AdminForm.prototype.elementInfoRequest = function elementInfoRequest() {
        this.mainClient.get(this.paintElements.bind(this), {});
    };

    /**
     * Abstract method to be implemented, validation of the information 
     * contained in the form.
     * @returns It should return an object with a boolean field call valid
     * indicating whether the validation is success and an object field
     * containing the values of the form or a string field called msg if 
     * the form is invalid.
     */
    AdminForm.prototype.validateFields = function validateFields() {        
    };

    /**
     * Make the request for creation of administration elements
     */
    AdminForm.prototype.createElementRequest = function createElementRequest() {
        // Validation of the form
        var validation = this.validateFields();

        // Make the request
        if (validation.valid) {
            this.mainClient.create(validation.data, this.elementInfoRequest.bind(this));
        } else {
            MessageManager.showMessage('Error', validation.msg);
        }
    };

    /**
     * Abstract method to be implemented, this method should fill
     * the concrete info and listener of every element of the list
     */
    AdminForm.prototype.fillListInfo = function fillListInfo(elements) {
    };

    /**
     * Paint the list of administration elements
     */
    AdminForm.prototype.paintElements = function paintElements(elements) {
        $('#admin-container').empty();

        if (elements.length > 0) {
            // Create the units list
            $.template('listTemplate', $('#list_template'));
            $.tmpl('listTemplate', {'title': 'Units'}).appendTo('#admin-container');

            // Lister for new unit form
            $('.add').click((function() {
                this.main = false;
                this.paintForm();
            }).bind(this));

            // The concrete content of the list is particular
            // of the concrete subclass
            this.fillListInfo(elements);
        } else {
            var msg = 'No elements registered, you may want to register one';
            var cont = $('<div></div>').addClass('admin-message');

            $('<a></a>').attr('id', 'back').text('Return').click((function() {
                backHandler(this);
            }).bind(this)).appendTo('#admin-container');

            cont.appendTo($('#admin-container'))
            MessageManager.showAlertInfo('Elements', msg, cont);
        }
        $('#back').click(paintElementTable);
    };

    /**
     * Abstract method to be implemented, this method allows to include
     * extra listeners in the form fields
     */
    AdminForm.prototype.setFormListeners = function setFormListeners() {
    };

    /**
     * Paint the create element form
     */
    AdminForm.prototype.paintForm = function paintForm() {
        $('#admin-container').empty();

        $.template('elementFormTemplate', this.formTemplate);
        $.tmpl('elementFormTemplate').appendTo('#admin-container');

        // Listener for back link
        $('#back').click((function() {
            backHandler(this);
        }).bind(this));

        // The concrete subclass may include extra listeners
        this.setFormListeners();

        // Listener for submit
        $('#elem-submit').click(this.createElementRequest.bind(this));
    };

})();