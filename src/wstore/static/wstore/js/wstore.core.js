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

(function () {

    paintMenuOffering = function paintMenuOffering(offeringElem, container, action, detailsContainer) {
        var offDetailsView = new CatalogueDetailsView(offeringElem, action, detailsContainer);
        var labelClass = "label";
        var labelValue = offeringElem.getState();
        var stars, templ, priceStr = 'Open';

        // Append Price and button if necessary
        $.template('miniOfferingTemplate', $('#mini_offering_template'));
        templ = $.tmpl('miniOfferingTemplate', {
            'name': offeringElem.getName(),
            'organization': offeringElem.getOrganization(),
            'logo': offeringElem.getLogo(),
            'description': offeringElem.getShortDescription()
        }).click((function(off) {
            return function() {
                off.showView();
            }
        })(offDetailsView));

        fillStarsRating(offeringElem.getRating(), templ.find('.stars-container'));

        if (!offeringElem.comments.length) {
            templ.find('.stars-container').css('opacity', '0.2');
        }

        if (!offeringElem.isOpen()) {
            priceStr = getPriceStr(offeringElem.getPricing());
        } else {
            templ.addClass('open-offering');
        }
        // Append button if needed
        if ((USERPROFILE.getCurrentOrganization() != offeringElem.getOrganization()) 
                && (labelValue == 'published') && !offeringElem.isOpen()) {
            var padding = '17px';
            var text = priceStr;
            var buttonClass = "btn btn-success";

            if (priceStr != 'Free') {
                buttonClass = "btn btn-blue";
            }

            if (priceStr == 'View pricing') {
                text = 'Acquire';
            }
            $('<button></button>').addClass(buttonClass + ' mini-off-btn').text(text).click((function(off) {
                return function() {
                    off.showView();
                    off.mainAction('Acquire');
                }
            })(offDetailsView)).css('padding-left', padding).css('overflow', 'hidden').css('height', '25px').appendTo(templ.find('.offering-meta'));
        } else {
            if (labelValue == 'rated' && offeringElem.isOpen()) {
                labelValue = 'published';
            }

            if (labelValue != 'published') {
                var label = $('<span></span>');
                if (labelValue == 'purchased' || labelValue == 'rated') {
                    labelClass += " label-success";
                    labelValue = 'purchased';
                } else if (labelValue == 'deleted') {
                    labelClass += " label-important";
                }

                if (labelValue == 'purchased') {
                    labelValue = 'acquired';
                }
                label.addClass(labelClass).text(labelValue);
                label.appendTo(templ.find('.offering-meta'));
            } else {
                var span = $('<span></span>').addClass('mini-off-price').text(priceStr);
                if (priceStr == 'Free' || priceStr == 'Open') {
                    span.css('color', 'green');
                }
                span.appendTo(templ.find('.offering-meta'));
            }
        }

        templ.appendTo(container)
    };
  /**
   *
   */
  WStore = {}
  
  //***********************************************************************************************
  // 'wstore/components.js'
  //***********************************************************************************************
  
  /**
   *
   */
  buildFormDefault = function buildFormDefault() {
    var $form;
    
    // Create the form defult
    $form = $('<form>').addClass('form form-default').append(
      $('<div>').addClass('form-errors row-fluid'),
      $('<div>').addClass('form-fields row-fluid'),
      $('<div>').addClass('form-options row-fluid')
    );
    
    return $form;
  };
  
  /**
   *
   */
  buildModalDefault = function buildModalDefault() {
    var $modal;
    
    // Create the modal default
    $modal = $('<div>').addClass('modal modal-default fade').append(
      $('<div>').addClass('modal-header').append(
        $('<button>').addClass('close').attr('type', 'button').attr('data-dismiss', 'modal').append('&times;'),
        $('<h3>').addClass('modal-title')
      ),
      $('<div>').addClass('modal-body'),
      $('<div>').addClass('modal-footer')
    );
    
    /*<span class="sending gif-loading hide"></span>*/
    
    return $modal;
  };
  
  /**
   *
   */
  buildMessage = function buildMessage(type, context) {
    var $message;
    
    context = context || {}; // Optional
    
    // Create the alert message
    $message = $('<div>').addClass('alert alert-'+type + ' alert-block fade in');
    
    // Add className
    if (context['className']) {
      $message.addClass(context.className);
    }
    
    // Add message body
    if (context['messageBody']) {
      $message.append(context.messageBody);
    }
    
    return $message;
  };
  
  /**
   *
   */
  buildPanelDefault = function buildPanelDefault(context) {
    var $panel;
    
    context = context || {}; // Optional
    
    // Create the panel default
    $panel = $('<div>').addClass('panel panel-default').append(
      $('<div>').addClass('panel-heading').append(
        $('<span>').addClass('panel-close'),
        $('<span>').addClass('panel-options')
      ),
      $('<div>').addClass('panel-body')
    );
    
    // Add title
    if (context['title']) {
      $panel.find('.panel-heading').prepend(context.title);
    }
    
    // Add options list
    if (context['options']) {
      for (var i in context.options) {
        $panel.find('.panel-options').append(context.options[i].addClass('option'));
      }
    }
    
    // Add action close
    if (context['close']) {
      $panel.find('.panel-close').append(context['close']);
    }
    
    return $panel;
  };
  
  /**
   *
   */
  buildFormOption = function buildFormOption(id, value, size, isSubmit) {
    var $option, className = 'basic', typeButton = 'button';
    
    if (isSubmit) {
      className = 'blue';
      typeButton = 'submit';
    }
    
    $option = $('<span>').addClass('span'+size.toString()).append(
      $('<input>').addClass('btn btn-'+className+' span12')
        .attr('id', id).attr('type', typeButton).val(value)
    );
    
    return $option;
  };
  
  WStore.components = {
    buildFormDefault: buildFormDefault,
    buildFormOption: buildFormOption,
    buildMessage: buildMessage,
    buildPanelDefault: buildPanelDefault,
    displayIconAdd: function displayIconAdd() {
      return $('<span>').addClass('icon-plus');
    },
    displayIconArrowLeft: function displayIconArrowLeft() {
      return $('<span>').addClass('icon-chevron-left');
    },
    displayIconArrowRight: function displayIconArrowRight() {
      return $('<span>').addClass('icon-chevron-right');
    },
    displayIconClose: function displayIconClose() {
      return $('<span>').addClass('icon-remove');
    },
    displayIconDelete: function displayIconDelete() {
      return $('<span>').addClass('icon-trash');
    },
    displayIconEdit: function displayIconEdit() {
      return $('<span>').addClass('icon-pencil');
    },
    displayIconGroup: function displayIconGroup() {
      return $('<span>').addClass('icon-group');
    },
    displayIconSuccess: function displayIconSuccess() {
      return $('<span>').addClass('icon-ok-sign');
    },
    displayIconUser: function displayIconUser() {
      return $('<span>').addClass('icon-user');
    },
    
  };
  
  //***********************************************************************************************
  // 'wstore/forms.js'
  //***********************************************************************************************
  
  /**
   * showFormErrors method
   */
  showFormErrors = function showFormErrors($formID, errorFields) {
    var $formErrors;
    
    // Empty the form errors
    $formErrors = $formID.find('.form-errors');
    $formErrors.hide().empty();
    
    // Clean the error fields
    $formID.find('.form-fields').find('.control-group').removeClass('error');
    
    
    if (errorFields.length > 0) {
      // Hide message if the field do not have errors
      $formID.find('input[type="text"], input[type="password"], select').focus(function () {
        if (!$(this).parent().parent().hasClass('error')) {
          $formErrors.hide(400).empty();
        }
      });
      
      // Build the error message if it is a error field
      $.each(errorFields, function(key, value) {
        $(value.field).parent().parent().addClass('error');
        $(value.field).focus(function () {
          if ($(this).parent().parent().hasClass('error')) {
            $formErrors.empty().show().append(
              buildMessage('error', {messageBody: '<strong>Error!</strong> '+value.message,})
            );
          }
        });
      });
      
      // Focus on the first error field
      $(errorFields[0].field).focus();
    }
  };
  
  /**
   * showResponseError method
   */
  showResponseError = function showResponseError($formID, message) {
    var $formErrors;
    
    // Empty the form errors
    $formErrors = $formID.find('.form-errors');
    $formErrors.hide().empty();
    
    // Clean the error fields
    $formID.find('.form-fields').find('.control-group').removeClass('error');
    
    $formErrors.empty().show().append(
      buildMessage('error', {messageBody: '<strong>Error!</strong> '+message,})
    );
    
    $formID.find('input[type="text"], input[type="password"], select').focus(function () {});
  };
  
  WStore.forms = {};
  WStore.forms.showFormErrors = showFormErrors;
  WStore.forms.showResponseError = showResponseError;
  
  //***********************************************************************************************
  // 'wstore/modals.js'
  //***********************************************************************************************
  
  /**
   * ModalManager class
   */
  ModalManager = function ModalManager(modalID) {
    this.modalID = modalID;
  };
  
  /**
   * showModal method
   */
  ModalManager.prototype.showModal = function showModal(context) {
    var $modal;
    
    // Clean the modal container
    
    $(this.modalID).empty();
    
    // Build the modal
    $modal = buildModalDefault();
    $modal.find('.modal-title').append(context.title);
    $modal.find('.modal-body').append(context.content);
    $modal.find('.modal-footer').append(
      $('<input>').attr('type', 'button').attr('id', 'modal-close').attr('data-dismiss', 'modal')
        .addClass('btn btn-basic').val('Cancel'),
      context.action
    );
    
    // Append the panel
    $(this.modalID).append($modal)
    
    // Show the modal created
    $modal.modal('show');
  };
  
  /**
   * showDeleteModal method
   */
  ModalManager.prototype.showDeleteModal = function showDeleteModal(context, deleteID) {
    context.action = $('<input>').attr('type', 'button').attr('id', deleteID).attr('data-dismiss', 'modal')
      .addClass('btn btn-danger').val('Delete');
    
    this.showModal(context);
  };
  
  WStore.modals = new ModalManager('#modal-message');
  
  //***********************************************************************************************
  // 'wstore/messages.js'
  //***********************************************************************************************
  
  /**
   * MessagesManager class
   */
  MessagesManager = function MessagesManager(messageID, timeout, className) {
    this.messageID = messageID;
    this.defaultTimeout = timeout;
    this.className = className;
  };
  
  /**
   * hideMessage method
   */
  MessagesManager.prototype.hideMessage = function hideMessage() {
    $(this.messageID).hide('slow').find('.alert').remove();
  };
  
  /**
   * showMessage method
   */
  MessagesManager.prototype.showMessage = function showMessage(type, $message, timeout) {
    var $alertMessage = buildMessage(type, {messageBody: $message, className: this.className});
    
    // Clean the previous message
    $(this.messageID).find('.alert').remove();
    
    // Append the new message
    $(this.messageID).append($alertMessage).show();
    
    // Apply the default timeout
    if (timeout) {
      setTimeout((function () {
        this.hideMessage();
      }).bind(this), this.defaultTimeout);
    }
    
  };
  
  /**
   * showErrorMessage method
   */
  MessagesManager.prototype.showErrorMessage = function showErrorMessage($message, timeout) {
    this.showMessage('error', $message, timeout);
  };
  
  /**
   * showInfoMessage method
   */
  MessagesManager.prototype.showInfoMessage = function showInfoMessage($message, timeout) {
    $message = $('<span>').append($('<span>').addClass('icon-info-sign'), ' ', $message);
    this.showMessage('info', $message, timeout);
  };
  
  /**
   * showSuccessMessage method
   */
  MessagesManager.prototype.showSuccessMessage = function showSuccessMessage($message, timeout) {
    $message = $('<span>').append($('<span>').addClass('icon-ok-sign'), ' ', $message);
    this.showMessage('success', $message, timeout);
  };
  
  WStore.messages = new MessagesManager('#alert-message', 3000, 'span6');
  
  //***********************************************************************************************
  // 'wstore/urls.js'
  //***********************************************************************************************
  
  /**
   * 
   */
  wstore_urlpatterns = {
    marketplaces: {
      collection: '/api/administration/marketplaces/',
      entry: '/api/administration/marketplaces/${name}',
    },
    organizations: {
      collection: '/api/administration/organizations/',
      entry: '/api/administration/organizations/${name}',
      user_collection: '/api/administration/organizations/${name}/users/',
    },
    repositories: {
      collection: '/api/administration/repositories/',
      entry: '/api/administration/repositories/${name}',
    },
    resources: {
      search: '/api/administration/search',
    },
    rss: {
      collection: '/api/administration/rss/',
      entry: '/api/administration/rss/${name}',
    },
    users: {
      collection: '/api/administration/profiles/',
      entry: '/api/administration/profiles/${username}/',
    },
  };
  
  /**
   * RequestManager class
   */
  RequestManager = function RequestManager(url) {
    this.url = url;
  };
  
  /**
   * request method
   */
  RequestManager.prototype.request = function request(method, context, parameters) {
    var response = {}, requestURL;
    
    requestURL = this.url;
    
    // Check the parameters
    if (typeof parameters != 'undefined') {
      requestURL = requestURL+'?'+parameters;
    }
    
    $.ajax({
      headers: {'X-CSRFToken': $.cookie('csrftoken'),},
      async: false,
      type: method,
      url: requestURL,
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(context),
      success: function (data) {
        // Build the success response
        response.noErrors = true;
        response.data = data;
      },
      error: function (xhr) {
        // Build the error response
        response.noErrors = false;
        response.message = JSON.parse(xhr.responseText).message;
      }
    });
    
    return response;
  };
  
  /**
   * create method
   */
  RequestManager.prototype.create = function create(context, parameters) {
    return this.request('POST', context, parameters);
  };
  
  /**
   * read method
   */
  RequestManager.prototype.read = function read(parameters) {
    return this.request('GET', '', parameters);
  };
  
  /**
   * update method
   */
  RequestManager.prototype.update = function update(context, parameters) {
    return this.request('PUT', context, parameters);
  };
  
  /**
   * destroy method
   */
  RequestManager.prototype.destroy = function destroy(parameters) {
    return this.request('DELETE', '', parameters);
  };
  
  /**
   * URLManager class
   */
  URLManager = function URLManager(urlpatterns) {
    this.urlpatterns = urlpatterns;
  };
  
  /**
   * getURLs method
   */
  URLManager.prototype.getURLs = function getURLs(namespace) {
    return new URLManager(this.urlpatterns[namespace]);
  };
  
  /**
   * getURL method
   */
  URLManager.prototype.getURL = function getURL(name, elements) {
    var piece, url;
    
    if (name.indexOf(':') > 0) {
      piece = name.split(':', 2);
      url = this.urlpatterns[piece[0]][piece[1]]
    } else {
      url = this.urlpatterns[name]
    }
    
    // Render elements
    for (var i in elements) {
      url = url.replace('${'+i+'}', elements[i]);
    }
    
    return new RequestManager(url);
  };
  
  WStore.urls = new URLManager(wstore_urlpatterns);
  
  //***********************************************************************************************
  // 'wstore/resources.js'
  //***********************************************************************************************
  
  WStore.resources = {};
  
  //***********************************************************************************************
  // 'wstore/resources/organizations.js'
  //***********************************************************************************************
  
  WStore.resources.organizations = {};
  
  //***********************************************************************************************
  // 'wstore/resources/organizations/forms.js'
  //***********************************************************************************************
  
  /**
   * OrganizationForm class
   */
  OrganizationForm = function OrganizationForm(formID, data) {
    this.data = {
      name: '',
      notification_url: '',
      tax_address: {
        tax_street: '',
        tax_postcode: '',
        tax_city: '',
        tax_province: '',
        tax_country: '',
      },
      payment_form: {
        card_type: '',
        card_number: '',
        card_code: '',
        card_expiry_month: '',
        card_expiry_year: '',
      },
    };
    this.fields = {
      name: 'input[name="name"]',
      notification_url: 'input[name="notification_url"]',
      tax_street: 'input[name="tax_street"]',
      tax_postcode: 'input[name="tax_postcode"]',
      tax_city: 'input[name="tax_city"]',
      tax_province: 'input[name="tax_province"]',
      tax_country: 'input[name="tax_country"]',
      card_type: 'select[name="card_type"]',
      card_number: 'input[name="card_number"]',
      card_code: 'input[name="card_code"]',
      card_expiry_month: 'select[name="card_expiry_month"]',
      card_expiry_year: 'select[name="card_expiry_year"]',
    };
    this.errors = [];
    this.formID = formID;
    
    data = data || {}; // Optional
    
    if (data) {
      if (data['name']) {
        this.data.name = data.name;
      }
      if (data['notification_url']) {
        this.data.notification_url = data.notification_url;
      }
      if (data['tax_address']) {
        for (var i in data.tax_address) {
          this.data.tax_address[i] = data.tax_address[i];
        }
      }
      if (data['payment_form']) {
        for (var i in data.payment_form) {
          this.data.payment_form[i] = data.payment_form[i];
        }
      }
    }
    
  };
  
  /**
   * buildContext method
   */
  OrganizationForm.prototype.buildContext = function buildContext() {
    var context = {}, nFilled = 0, nFields = 0;

    context.name = this.data.name;
    context.notification_url = this.data.notification_url;

    for (var i in this.data.tax_address) {
      if (this.data.tax_address[i] != "") {
        nFilled += 1;
      }
      nFields += 1;
    }

    if (nFilled > 0 && nFilled == nFields) {
      context.tax_address = {};
      context.tax_address.street = this.data.tax_address.tax_street;
      context.tax_address.postal = this.data.tax_address.tax_postcode;
      context.tax_address.city = this.data.tax_address.tax_city;
      context.tax_address.province = this.data.tax_address.tax_province;
      context.tax_address.country = this.data.tax_address.tax_country;
    }

    nFilled = 0;
    nFields = 0;

    for (var i in this.data.payment_form) {
      if (this.data.payment_form[i] != "") {
        nFilled += 1;
      }
      nFields += 1;
    }

    if (nFilled > 0 && nFilled == nFields) {
      context.payment_info = {};
      context.payment_info.type = this.data.payment_form.card_type;
      context.payment_info.number = this.data.payment_form.card_number;
      context.payment_info.cvv2 = this.data.payment_form.card_code;
      context.payment_info.expire_month = this.data.payment_form.card_expiry_month;
      context.payment_info.expire_year = this.data.payment_form.card_expiry_year;
    }

    // Include field for identifying the user view
    // for the creation of organization
    context.is_user = true;
    return context;
  };
  
  /**
   * displayForm method
   */
  OrganizationForm.prototype.displayForm = function displayForm($templateID, $taTemplateID) {
    var currentDate = new Date(), $form, $formFields, $expiryYear;
    
    // Create the form template
    $.template('organization_form', $templateID);
    $formFields = $.tmpl('organization_form');
    
    // Add the tax-address form template
    $.template('ta_fields', $taTemplateID);
    
    // Build the default form
    $form = buildFormDefault();
    $form.find('.form-fields').append($formFields);
    $form.find('#id_org_ta_fields').append($.tmpl('ta_fields'));
    
    // Fill the organization fields
    $form.find(this.fields.name).val(this.data.name);
    $form.find(this.fields.notification_url).val(this.data.notification_url);
    
    // Fill the tax-address fields
    for (var i in this.data.tax_address) {
      $form.find(this.fields[i]).val(this.data.tax_address[i]);
    }
    
    // Add id
    $form.attr('id', this.formID);
    
    return $form;
  };
  
  /**
   * getData method
   */
  OrganizationForm.prototype.getData = function getData() {
    
    // Update the data of the fields
    this.data.name = $.trim($(this.fields.name).val());
    this.data.notification_url = $.trim($(this.fields.notification_url).val());
    
    for (var i in this.data.tax_address) {
      this.data.tax_address[i] = $.trim($(this.fields[i]).val());
    }
    
    for (var i in this.data.payment_form) {
      this.data.payment_form[i] = $.trim($(this.fields[i]).val());
    }
    
    return this.data;
  };
  
  /**
   * getErrors method
   */
  OrganizationForm.prototype.getErrors = function getErrors() {
    return this.errors;
  };
  
  /**
   * isValid method
   */
  OrganizationForm.prototype.isValid = function isValid() {
    var data = this.getData(), valid = true;
    var url_re = /(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
    var nFilled = 0, nFields = 0;
    
    // Clean the errors list
    this.errors = [];
    
    // Check the name field
    if (!data.name) {
      valid = false;
      this.errors.push({
        field: this.fields.name,
        message: 'The name field is required.'
      });
    }
    
    if (data.name && !/^[\w\s-]+$/.test(data.name)) {
      valid = false;
      this.errors.push({
        field: this.fields.name,
        message: 'Enter a valid name.'
      });
    }
    
    // Check the notification url field
    if (data.notification_url && !url_re.test(data.notification_url)) {
      valid = false;
      this.errors.push({
        field:this.fields.notification_url,
        message: 'Enter a valid URL.'
      });
    }
    
    // Check the tax address fields
    for (var i in data.tax_address) {
      if (data.tax_address[i] != '') {
        nFilled += 1;
      }
      nFields += 1;
    }
    
    if (nFilled > 0 && nFilled != nFields) {
      valid = false;
      for (var i in data.tax_address) {
        if (data.tax_address[i] == '') {
          this.errors.push({
            field:this.fields[i],
            message: 'All fields are required to provide a tax address.'
          });
        }
      }
    }
    
    nFilled = 0;
    nFields = 0;
    
    // Check the credit card fields
    for (var i in data.payment_form) {
      if (data.payment_form[i] != '') {
        nFilled += 1;
      }
      nFields += 1;
    }
    
    if (nFilled > 0 && nFilled != nFields) {
      valid = false;
      for (var i in data.payment_form) {
        if (data.payment_form[i] == '') {
          this.errors.push({
            field:this.fields[i],
            message: 'All fields are required to provide a credit card.'
          });
        }
      }
    }
    
    return valid;
  };
  
  /**
   * OrganizationUserForm class
   */
  OrganizationUserForm = function OrganizationUserForm(formID) {
    // default settings
    this.data = {
      username: '',
      roles: {
        role_customer: false,
        role_manager: false,
        role_provider: false,
      },
    };
    this.errors = [];
    this.fields = {
      username: 'input[name="username"]',
      role_customer: 'input[name="role_customer"]',
      role_manager: 'input[name="role_manager"]',
      role_provider: 'input[name="role_provider"]',
    };
    this.formID = formID;
  };
  
  /**
   * buildContext method
   */
  OrganizationUserForm.prototype.buildContext = function buildContext() {
    var context = {}, nFilled = 0, nFields = 0;
    
    context.user = this.data.username;
    context.roles = [];
    
    for (var i in this.data.roles) {
      if (this.data.roles[i] == true) {
        context.roles.push($(this.fields[i]).val());
      }
    }
    
    return context;
  };
  
  /**
   * displayForm method
   */
  OrganizationUserForm.prototype.displayForm = function displayForm($templateID) {
    var $form, $formFields;

    // Create the form template
    $.template('organization_user_form', $templateID);
    $formFields = $.tmpl('organization_user_form');

    // Build the default form
    $form = buildFormDefault();
    $form.attr('id', this.formID).find('.form-fields').append($formFields);

    return $form;
  };
  
  /**
   * getData method
   */
  OrganizationUserForm.prototype.getData = function getData() {

    // Update the data of the fields
    this.data.username = $.trim($(this.fields.username).val());

    for (var i in this.data.roles) {
      this.data.roles[i] = $(this.fields[i]).prop('checked');
    }

    return this.data;
  };
  
  /**
   * getErrors method
   */
  OrganizationUserForm.prototype.getErrors = function getErrors() {
    return this.errors;
  };
  
  /**
   * isValid method
   */
  OrganizationUserForm.prototype.isValid = function isValid() {
    var data = this.getData(), valid = true;
    
    // Clean the errors list
    this.errors = [];
    
    // Check the username field
    if (!data.username) {
      valid = false;
      this.errors.push({
        field: this.fields.username,
        message: 'The username field is required.'
      });
    }
    
    return valid;
  };
  
  WStore.resources.organizations.forms = {};
  WStore.resources.organizations.forms.OrganizationForm = OrganizationForm;
  WStore.resources.organizations.forms.OrganizationUserForm = OrganizationUserForm;
  
  //***********************************************************************************************
  // 'wstore/resources/organizations/urls.js'
  //***********************************************************************************************
  
  WStore.resources.organizations.urls = WStore.urls.getURLs('organizations');
  
  //***********************************************************************************************
  // 'wstore/resources/organizations/utils.js'
  //***********************************************************************************************
  
  /**
   * buildOrganizationData method
   */
  buildOrganizationData = function buildOrganizationData(data) {
    var newData = {};
    
    newData.name = data.name;
    newData.notification_url = data.notification_url;

    if (data['tax_address']) {
      newData.tax_address = {
        tax_street: data['tax_address']['street'],
        tax_postcode: data['tax_address']['postal'],
        tax_city: data['tax_address']['city'],
        tax_province: data['tax_address']['province'],
        tax_country: data['tax_address']['country']
      };
    }
    
    return newData;
  };
  
  /**
   * listOrganizations method
   */
  listOrganizations = function listOrganizations(username) {
    var response, isEmpty = true, organizations = {}, queryset = undefined;
    
    if (username) {
      queryset = "username="+username;
    }
    response = WStore.urls.getURL('organizations:collection').read(queryset);
    
    if (response.noErrors) {
      if (response.data.length > 0) {
        isEmpty = false;
        for (var i in response.data) {
          organizations[response.data[i].name] = buildOrganizationData(response.data[i]);
        }
      }
    }
    
    return {'isEmpty': isEmpty, 'list': organizations};
  };
  
  WStore.resources.organizations.utils = {};
  WStore.resources.organizations.utils.listOrganizations = listOrganizations;
  WStore.resources.organizations.utils.buildOrganizationData = buildOrganizationData;
  
  //***********************************************************************************************
  // 'wstore/resources/organizations/views.js'
  //***********************************************************************************************
  
  WStore.resources.organizations.views = {
    registrationView: function registrationView(form) {
      var response, successfully = false;
      
      if (form.isValid()) {
        response = WStore.urls
          .getURL('organizations:collection')
          .create(form.buildContext());
        if (response.noErrors) {
          successfully = true;
        } else {
          WStore.forms.showResponseError($('#'+form.formID), response.message);
        }
      } else {
        WStore.forms.showFormErrors($('#'+form.formID), form.getErrors());
      }
      return successfully;
    },
    userRegistrationView: function userRegistrationView(name, form) {
      var response, successfully = false;
      
      if (form.isValid()) {
        response = WStore.urls
          .getURL('organizations:user_collection', {'name': name})
          .create(form.buildContext());
        if (response.noErrors) {
          successfully = true;
        } else {
          WStore.forms.showResponseError($('#'+form.formID), response.message);
        }
      } else {
        WStore.forms.showFormErrors($('#'+form.formID), form.getErrors());
      }
      return successfully;
    },
    editionView: function editionView(name, form) {
      var response, successfully = false;
      
      if (form.isValid()) {
        response = WStore.urls
          .getURL('organizations:entry', {'name': name})
          .update(form.buildContext());
        if (response.noErrors) {
          successfully = true;
        } else {
          WStore.forms.showResponseError($('#'+form.formID), response.message);
        }
      } else {
        WStore.forms.showFormErrors($('#'+form.formID), form.getErrors());
      }
      return successfully;
    },
  };
  
})();
