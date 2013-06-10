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

        reader.onload = (function(file) {
            return function(e) {
                // Needs a sha-1 checksum in order to detect transmission problems
                var binaryContent = e.target.result;
                resource = {};
                resource.data = btoa(binaryContent);
                resource.name = file.name;
            }
        })(f);
        reader.readAsBinaryString(f);
    };

    var makeRegisterResRequest = function makeRegisterResRequest (evnt) {
         var name, version, link, contentType, request = {};

         evnt.preventDefault();
         name = $.trim($('[name="res-name"]').val());
         version = $.trim($('[name="res-version"]').val());
         link = $.trim($('[name="res-link"]').val());
         contentType = $.trim($('[name="res-content-type"]').val());
         description = $.trim($('[name="res-description"]').val());

         if (name && version) {
             if ($('[name="res-type"]').val() == 'download') {
                 request.content_type = contentType
             }
             csrfToken = $.cookie('csrftoken');
             request.name = name;
             request.version = version;
             request.description = description;
             request.type = $('[name="res-type"]').val();

             if (resource) {
                 request.content = resource;
             } else if (link) {
                 request.link = link;
             } else {
                 MessageManager.showMessage('Error', 'You have not added a resource');
                 return;
             }

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
                     MessageManager.showMessage('Created', 'The resource has been registered');
                 },
                 error: function (xhr) {
                     var resp = xhr.responseText;
                     var msg = JSON.parse(resp).message;
                     MessageManager.showMessage('Error', msg);
                 }
             });
         } else {
             MessageManager.showMessage('Error', 'missing a required field');
         }

    
    };

    showRegisterResourceForm = function showRegisterResourceForm() {
        resource = null;
        // Creates the modal
        MessageManager.showMessage('Register new resource', '');

        $.template('registerResTemplate', $('#register_res_form_template'));
        $.tmpl('registerResTemplate', {}).appendTo('.modal-body');

        //Set listeners
        $('#upload-help').on('hover', function () {
            $('#upload-help').popover('show');
        })
        $('#link-help').on('hover', function () {
            $('#link-help').popover('show');
        })

        $('[name="res-type"]').on('change', function() {
            if ($(this).val() == 'api') {
                $('[name="res-content-type"]').addClass('hide');
                $('#upload').addClass('hide');
                $('label:contains(Content type)').addClass('hide');
                $('label:contains(Upload resource)').addClass('hide');
                $('#upload-help').addClass('hide');
            } else {
                $('[name="res-content-type"]').removeClass('hide');
                $('#upload').removeClass('hide');
                $('label:contains(Content type)').removeClass('hide');
                $('label:contains(Upload resource)').removeClass('hide');
                $('#upload-help').removeClass('hide');
            }
        });

        $('#upload').on('change', handleResourceSelection);
        $('.modal-footer > .btn').click(makeRegisterResRequest);
    };

})();
