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
        
    $container
      .empty()
      .append(form.displayForm($('#organization_form_template'), $('#id_tmpl_pf_fields'), $('#id_tmpl_ta_fields')))
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
    
    $container
      .empty()
      .append(form.displayForm($('#id_tmpl_orgusr_form')))
      .find('.form-options').append(
        $('<span>').addClass('span6'),
        WStore.components.buildFormOption('pnl_orgusr-close', 'Cancel', 3, false),
        WStore.components.buildFormOption('pnl_orgusr-submit', 'Add user', 3, true)
      );
    
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
    
    $container.find('#id_org_inf_name').append(data.name);
    $container.find('#id_org_inf_notification_url').append(data.notification_url);
    
    if (data['tax_address']) {
      $container.find('#id_org_inf_tax_street').append(data.tax_address.tax_street);
      $container.find('#id_org_inf_tax_postcode').append(data.tax_address.tax_postcode);
      $container.find('#id_org_inf_tax_city').append(data.tax_address.tax_city);
      $container.find('#id_org_inf_tax_country').append(data.tax_address.tax_country);
    }
    
    if (data['payment_form']) {
      $container.find('#id_org_inf_card_type').append(data.payment_form.card_type);
      $container.find('#id_org_inf_card_number').append(data.payment_form.card_number);
      $container.find('#id_org_inf_card_code').append(data.payment_form.card_code);
      $container.find('#id_org_inf_card_expiry_month').append(data.payment_form.card_expiry_month);
      $container.find('#id_org_inf_card_expiry_year').append(data.payment_form.card_expiry_year);
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
          $('<a>').addClass('mdl-delete').attr('title', 'Delete')
            .append(WStore.components.displayIconDelete())
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
    
    $('.mdl-delete').click(function () {
      WStore.modals.showDeleteModal({
        title: 'Delete this organization',
        content: $('<span>')
          .append('Once you delete the <strong>'+name+'</strong> organization, there is no going back. Are you sure you want to proceed?'),
      }, 'unit-delete');
      $('#unit-delete').click(function (event) {
        self.initView();
        WStore.messages.showSuccessMessage('The <strong>'+name+'</strong> organization was removed successfully.', true);
        $('.modal').modal('hide');
        return false;
      });
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
      .append(form.displayForm($('#organization_form_template'), $('#id_tmpl_pf_fields'), $('#id_tmpl_ta_fields')));
    
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
      .append(form.displayForm($('#organization_form_template'), $('#id_tmpl_pf_fields'), $('#id_tmpl_ta_fields')));
    
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
          WStore.messages.showSuccessMessage('The <strong>'+form.data.name+'</strong> organization was created successfully.', true);
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
  
  organizationsTemplate = new OrganizationsPanels('organizations');
  
  refreshView = function refreshView() {
    organizationsTemplate.initView();
  };
  
})();