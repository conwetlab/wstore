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

    var resource;

    var handleResourceSelection = function handleResourceSelection (evnt) {
        var f = evnt.target.files[0];
        var reader = new FileReader();
        resource = {};

        reader.onload = (function(file) {
            return function(e) {
                // Needs a sha-1 checksum in order to detect transmission problems
                var binaryContent = e.target.result;
                // Check name format
                var nameReg = new RegExp(/^[\w\s-]+\.[\w]+$/);

                if (!nameReg.test(file.name)) {
                    resource.error = true;
                    resource.msg = 'Invalid file: Unsupported character in file name';
                } else {
                    resource.data = btoa(binaryContent);
                    resource.name = file.name;
                }
            }
        })(f);
        reader.readAsBinaryString(f);
    };

    var helpHandler = function helpHandler(evnt) {
        var helpId = evnt.target;
        if (!$(helpId).prop('displayed')) {
            $(helpId).popover('show');
            $(helpId).prop('displayed', true);
            $(helpId).addClass('question-sing-sel');
            // Add document even
            evnt.stopPropagation();
            $(document).click(function() {
                $(helpId).popover('hide');
                $(helpId).prop('displayed', false);
                $(helpId).removeClass('question-sing-sel');
                $(document).unbind('click');
            });
        }
    };

    var makeRegisterResRequest = function makeRegisterResRequest (evnt) {
         var name, version, link, contentType, request = {};
         var msg, error = false;

         evnt.preventDefault();
         evnt.stopPropagation();

         name = $.trim($('[name="res-name"]').val());
         version = $.trim($('[name="res-version"]').val());
         link = $.trim($('[name="res-link"]').val());
         contentType = $.trim($('[name="res-content-type"]').val());
         description = $.trim($('[name="res-description"]').val());

         if (!name || !version) {
             error = true;
             msg = 'Missing required field(s):';
             if (!name) {
                 msg += ' Name';
             }
             if (!version) {
                 msg += ' Version';
             }
         }

         // Check name format
         var nameReg = new RegExp(/^[\w\s-]+$/);
         if (name && !nameReg.test(name)) {
             error = true;
             msg = 'Invalid name format: Unsupported character';
         }

         request.content_type = contentType
         csrfToken = $.cookie('csrftoken');
         request.name = name;
         request.version = version;
         request.description = description;
         request.open = $('#res-open').prop('checked');

         if (!$.isEmptyObject(resource)) {
             // Check resource
             if (resource.error) {
                 error = true;
                 msg = resource.msg;
             } else {
                 request.content = resource;
             }
         } else if (link) {
             // Check link format
             var urlReg = new RegExp(/(http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/);
             if (!urlReg.test(link)) {
                 error = true;
                 msg = 'Invalid URL format';
             } else {
                 request.link = link;
             }
         } else {
             error = true;
             msg = 'You have not added a resource';
         }

         if (!error) {
             $('#loading').removeClass('hide'); // Loading view when waiting for requests
             $('#loading').css('height', $(window).height() + 'px');
             $('#message').modal('hide');
             $.ajax({
                 headers: {
                     'X-CSRFToken': csrfToken,
                 },
                 type: "POST",
                 url: EndpointManager.getEndpoint('RESOURCE_COLLECTION'),
                 dataType: 'json',
                 contentType: 'application/json',
                 data: JSON.stringify(request),
                 success: function (response) {
                     $('#loading').addClass('hide');
                     MessageManager.showMessage('Created', 'The resource has been registered');
                 },
                 error: function (xhr) {
                     $('#loading').addClass('hide');
                     var resp = xhr.responseText;
                     var msg = JSON.parse(resp).message;
                     MessageManager.showMessage('Error', msg);
                 }
             });
         } else {
             MessageManager.showAlertError('Error', msg, $('#error-container'));
         }

    
    };

    showRegisterResourceForm = function showRegisterResourceForm() {
        resource = null;
        // Creates the modal
        MessageManager.showMessage('Register new resource', '');

        $.template('registerResTemplate', $('#register_res_form_template'));
        $.tmpl('registerResTemplate', {}).appendTo('.modal-body');


        // Configure help messages
        $('#upload-help').popover({'trigger': 'manual'});
        $('#link-help').popover({'trigger': 'manual'});
        $('#open-help').popover({'trigger': 'manual'});

        //Set listeners
        $('#upload-help').click(helpHandler);
        $('#link-help').click(helpHandler);
        $('#open-help').click(helpHandler);

        $('#message').on('hide', function() {
            $(document).unbind('click');
            $('.popover').remove();
        });

        $('#res-type').on('change', function() {
            resource = {};
            $('[name="res-link"]').val('');
            if ($(this).val() == 'upload') {
                $('#upload').removeClass('hide');
                $('#upload-help').removeClass('hide');
                $('[name="res-link"]').addClass('hide');
                $('#link-help').addClass('hide');
            } else {
                $('#upload').addClass('hide');
                $('#upload-help').addClass('hide');
                $('[name="res-link"]').removeClass('hide');
                $('#link-help').removeClass('hide');
            }
        });

        $('#upload').on('change', handleResourceSelection);
        $('.modal-footer > .btn').click(makeRegisterResRequest);
    };

})();
