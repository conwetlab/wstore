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
  
  //***********************************************************************************************
  // 'wstore/resources/organizations/panels.js'
  //***********************************************************************************************
  
  /**
   *
   */
  OrganizationsPanels = function OrganizationsPanels(selector, selectorMessage, selectorModal) {
    this.selector = selector;
    this.organizations = {};
    this.methods = WStore.resources.organizations;
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.closePanelContainer = function closePanelContainer() {
    
    // Destroy the container
    $('.organizations-container').remove();
    
    // Clean the active class of action add
    $('.organizations-add')
      .removeClass('active')
      .find('span')
      .removeClass('icon-minus')
      .addClass('icon-plus');
    
    // Clean the active class of all units
    $('td[class*="organizations-"]')
      .removeClass('active')
      .find('.icon-chevron-left')
      .attr('class', 'icon-chevron-right');
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.displayPanelList = function displayPanelList() {
    var context = {}, $panel, $tableContainer;
    
    $('.organizations')
      .remove('.organizations-menu')
      .append($('<div>').addClass('organizations-menu span4'));
    
    
    // Create the context for the panel
    context.title = $('<span>').append(WStore.components.displayIconGroup, ' Organizations');
    context.close = $('<a>').addClass('organizations-add').attr('title', 'Add Organization').append(WStore.components.displayIconAdd);
    
    // Display the default panel from WStore
    $panel = WStore.components.buildPanelDefault(context);
    
    // Append the default table
    $panel.find('.panel-body').append($('<table>').addClass('table table-default').append($('<tbody>')));
    $tableContainer = $panel.find('tbody');
    
    // List all organizations
    $.each(this.organizations, function (name, data) {
      $('<tr>').append(
          $('<td>').addClass('organizations-'+name)
            .append(
              name,
              $('<span>').addClass('pull-right').append(WStore.components.displayIconArrowRight))
        )
        .appendTo($tableContainer)
    });
    
    $('.organizations-menu').append($panel);
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.editionPanel = function editionPanel($container, data, $actived) {
    var form, self = this;
    
    form = new this.methods.forms.OrganizationForm('registration_form', data);
    
    $actived.addClass('active');
    
    $('.organizations-container').find('.panel-heading span.extend_title').remove();
    $('.organizations-container').find('.panel-heading span.panel-close')
      .before('<span class="extend_title"> / Edit information</span>');
    
    $container
      .empty()
      .append(form.displayForm($('#organization_form_template'), $('#id_tmpl_ta_fields')))
      .find('.form-options').append(
        $('<span>').addClass('span6'),
        WStore.components.buildFormOption('pnl_edit-close', 'Cancel', 3, false),
        WStore.components.buildFormOption('pnl_edit-submit', 'Save changes', 3, true)
      );
    
    $container
      .find('input[name="name"]').prop('readonly', true);
    
    $container
      .find('#pnl_edit-close')
      .click(function (event) {
        $actived.removeClass('active');
        self.infoPanel($container, data);
        return false;
      });
    
    $container
      .find('#registration_form')
      .submit(function (event) {
        if (self.methods.views.editionView(data.name, form)) {
          self.initView();
          WStore.messages.showSuccessMessage('The <strong>'+data.name+'</strong> organization was changed successfully.', true);
        }
      return false;
    });
  };
  
  OrganizationsPanels.prototype.usersPanel = function usersPanel($container, data, $actived) {
    var form, self = this;
    
    form = new this.methods.forms.OrganizationUserForm('user_registration');
    
    $actived.addClass('active');
    
    $('.organizations-container').find('.panel-heading span.extend_title').remove();
    $('.organizations-container').find('.panel-heading span.panel-close')
      .before('<span class="extend_title"> / Members</span>');
    
    $container
      .empty()
      .append(form.displayForm($('#id_tmpl_orgusr_form')))
      .find('.form-options').append(
        $('<span>').addClass('span6'),
        WStore.components.buildFormOption('pnl_orgusr-close', 'Cancel', 3, false),
        WStore.components.buildFormOption('pnl_orgusr-submit', 'Add user', 3, true)
      );
    
    $container
      .prepend(
        $('<table>').addClass('table table-bordered table-members').append($('<thead>').append(
          $('<tr>').append('<th class="username">Username</th>',
                           '<th class="role_customer">Customer</th>',
                           '<th class="role_manager">Manager</th>',
                           '<th class="role_provider">Provider</th>')
          ), $('<tbody>').addClass('organization_users_list')
        )
      );
    
    response = WStore.urls.getURL('resources:search').read('namespace=user&q=username:*');
    users = response.data.results;

    options = '[';
    
    for (var u in users) {
      options += '"'+users[u].username+'",';
    }
    
    options = options.substring(0, options.length-1) + ']';

    $container
      .find('#user_registration input[name="username"]')
      .attr('autocomplete', 'off')
      .attr('data-provide', 'typeahead')
      .attr('data-items', '4') 
      .attr('data-source', options);
    
    response = this.methods.urls.getURL('user_collection', {name: data.name}).read();
    $users_table = $container.find('.organization_users_list');
    
    if (response.noErrors) {
      
      for (var i in response.data.members) {
        user = response.data.members[i];
        customer = false;
        manager = false;
        provider = false;
        
        $user_tr = $('<tr>');
        $user_tr.append('<td class="username">'+user.username+'</td>');
        for (var j in user.roles) {
          if (user.roles[j] == 'customer') {
            customer = true;
          }
          if (user.roles[j] == 'manager') {
            manager = true;
          }
          if (user.roles[j] == 'provider') {
            provider = true;
          }
        }
        if (customer == true) {
          $user_tr.append('<td><icon class="icon-ok-sign"></icon></td>');
        } else {
          $user_tr.append('<td></td>');
        }
        if (manager == true) {
          $user_tr.append('<td><icon class="icon-ok-sign"></icon></td>');
        } else {
          $user_tr.append('<td></td>');
        }
        if (provider == true) {
          $user_tr.append('<td><icon class="icon-ok-sign"></icon></td>');
        } else {
          $user_tr.append('<td></td>');
        }
        $users_table.append($user_tr);
      }
    }
    
    $container
      .find('#pnl_orgusr-close')
      .click(function (event) {
        $actived.removeClass('active');
        self.infoPanel($container, data);
        return false;
      });
    
    $container
      .find('#user_registration')
      .submit(function (event) {
        if (self.methods.views.userRegistrationView(data.name, form)) {
          self.initView();
          WStore.messages.showSuccessMessage('The <strong>'+form.data.username+'</strong> user was added to the <strong>'+data.name+'</strong> organization successfully.', true);
        }
        return false;
      });
    
  };
  
  OrganizationsPanels.prototype.infoPanel = function infoPanel($container, data) {
    var form;
    
    $.template('info_form', $('#id_tmpl_org_inf'));
    
    $container
      .empty()
      .append($.tmpl('info_form'));
    
    $('.organizations-container').find('.panel-heading span.extend_title').remove();
    
    $container.find('#id_org_inf_name').append(data.name);
    $container.find('#id_org_inf_notification_url').append(data.notification_url);
    
    if (data['tax_address']) {
      $container.find('#id_org_inf_tax_street').append(data.tax_address.tax_street);
      $container.find('#id_org_inf_tax_postcode').append(data.tax_address.tax_postcode);
      $container.find('#id_org_inf_tax_city').append(data.tax_address.tax_city);
      $container.find('#id_org_inf_tax_province').append(data.tax_address.tax_province);
      $container.find('#id_org_inf_tax_country').append(data.tax_address.tax_country);
    }
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.unitPanel = function unitPanel($unit, name, data) {
    var self = this, $panel;
    
    $('.organizations')
      .remove('.organizations-container')
      .append($('<div>').addClass('organizations-container span6'));
    
    $panel = WStore.components.buildPanelDefault({
        title: name + ' organization',
        options: [
          $('<a>').addClass('pnl_edit').attr('title', 'Edit')
            .append(WStore.components.displayIconEdit()),
          $('<a>').addClass('pnl_orgusr').attr('title', 'Add User')
            .append(WStore.components.displayIconUser()),
        ],
        close: $('<a>').addClass('pnl_unit-close').attr('title', 'Close')
          .append(WStore.components.displayIconClose()),
      });
    
    $('.organizations-container').append($panel);
    
    $('.pnl_edit').click(function () {
      if (!$(this).hasClass('active')) {
        $panel.find('.panel-heading').find('.active').removeClass('active');
        self.editionPanel($panel.find('.panel-body'), data, $(this));
      }
      return false;
    });
    
    $('.pnl_orgusr').click(function () {
      if (!$(this).hasClass('active')) {
        $panel.find('.panel-heading').find('.active').removeClass('active');
        self.usersPanel($panel.find('.panel-body'), data, $(this));
      }
      return false;
    });
    
    $('.pnl_unit-close').click(function () {
      $unit.trigger('click');
      return false;
    });
    
    this.infoPanel($panel.find('.panel-body'), data);
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.registrationPanel = function registrationPanel() {
    var self = this, $panel, context = {}, form;
    
    form = new this.methods.forms.OrganizationForm('registration_form');
    
    $('.organizations')
      .remove('.organizations-container')
      .append($('<div>').addClass('organizations-container span6'));
    
    $panel = WStore.components.buildPanelDefault({
        title: 'New organization',
        close: $('<a>').addClass('pnl_record-close')
          .attr('title', 'Close')
          .append(WStore.components.displayIconClose()),
      });
    
    $panel
      .find('.panel-body')
      .append(form.displayForm($('#organization_form_template'), $('#id_tmpl_ta_fields')));
    
    $panel
      .find('.form-options').append(
        $('<span>').addClass('span9'),
        WStore.components.buildFormOption('pnl_record-submit', 'Create', 3, true)
    );
    
    $('.organizations-container').append($panel);
    
    $('.pnl_record-close').click(function () {
      $('.organizations-add').trigger('click');
      return false;
    });
    
    $('.organizations-container')
      .find('#registration_form')
      .submit(function (event) {
        if (self.methods.views.registrationView(form)) {
          readyHandler();
          //self.initView();
          WStore.messages.showSuccessMessage('The <strong>'+form.data.name+'</strong> organization was created successfully.', true);
        }
        return false;
      });
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.firstRegistrationPanel = function firstRegistrationPanel() {
    var self = this, $panel, context = {}, form;
    
    form = new this.methods.forms.OrganizationForm('registration_form');
    
    $('.organizations')
      .append($('<div>').addClass('record_container span6'));
    
    $panel = WStore.components.buildPanelDefault({
        title: 'New organization',
        close: $('<a>').addClass('pnl_record-close')
          .attr('title', 'Close')
          .append(WStore.components.displayIconClose()),
      });
    
    $panel
      .find('.panel-body')
      .append(form.displayForm($('#organization_form_template'), $('#id_tmpl_ta_fields')));
    
    $panel
      .find('.form-options').append(
        $('<span>').addClass('span9'),
        WStore.components.buildFormOption('pnl_record-submit', 'Create', 3, true)
    );
    
    $('.record_container').append($panel);
    
    $('.pnl_record-close').click(function () {
      $('#alert-message').show();
      $('.record_container').remove();
      return false;
    });
    
    $('.record_container')
      .find('#registration_form')
      .submit(function (event) {
        if (self.methods.views.registrationView(form)) {
          self.initView();
          $('#alert-message').show();
          WStore.messages.showSuccessMessage('The <strong>' + form.data.name + '</strong> organization was created successfully.', true);
        }
        return false;
      });
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.initView = function initView() {
    var response;
    
    $('.organizations').empty();
    
    response = this.methods.utils.listOrganizations(USERNAME);
    
    if (!response.isEmpty) {
      this.organizations = response.list;
      this.listView();
    } else {
      this.emptyView();
    }
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.listView = function listView() {
    var self = this;
    
    $('.organizations').append($('<div>').addClass('span1'), $('<div>').addClass('offset span3'));
    this.displayPanelList();
    
    $('.organizations-add').click(function (event) {
      if (!$(this).hasClass('active')) {
        self.closePanelContainer();
        $(this).addClass('active').find('span').attr('class', 'icon-minus');
        $('.offset').hide(250, function() {
          self.registrationPanel();
        });
      } else {
        self.closePanelContainer();
        $('.offset').show(250);
      }
      return false;
    });
    
    $.each(this.organizations, function (name, data) {
      $('.organizations-'+name).click(function (event) {
        var $unit = $(this);
        if (!$(this).hasClass('active')) {
          self.closePanelContainer();
          $(this).addClass('active').find('.icon-chevron-right').attr('class', 'icon-chevron-left');
          $('.offset').hide(250, function() {
            self.unitPanel($unit, name, data);
          });
        } else {
          self.closePanelContainer();
          $('.offset').show(250);
        }
        return false;
      });
    });
    
  };
  
  /**
   *
   */
  OrganizationsPanels.prototype.emptyView = function emptyView() {
    var self = this;
    var messageBody = 'No organizations created yet. To register one, <a href class="pnl-add">click here</a>.';
    
    WStore.messages.showInfoMessage(messageBody, false);
    $('.'+this.selector).empty();
    $('.pnl-add').click(function (event) {
      $('#alert-message').hide();
      $('.organizations').empty().append('<div class="span3"></div>')
      self.firstRegistrationPanel();
      return false;
    });
  };

  OrganizationsPanels.prototype.setWidth = function setWidth() {
      var width = $(window).width() - 255;
      if (width > 0) {
          $('.organizations').css('width', width + 'px');
      }
  };

  organizationsTemplate = new OrganizationsPanels('organizations');
  
  paintOrganizationsView = function paintOrganizationsView() {
    var mpainter = new MenuPainter();
    mpainter.setState('first');
    organizationsTemplate.initView();
    organizationsTemplate.setWidth();
    $(window).resize(organizationsTemplate.setWidth);
  };
  
})();