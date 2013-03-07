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
         var name, version, link, request = {};

         evnt.preventDefault();
         name = $('[name="res-name"]').val();
         version = $('[name="res-version"]').val();
         link = $('[name="res-link"]').val();
         description = $('[name="res-description"]').val();

         if (name && version) {
             csrfToken = $.cookie('csrftoken');
             request.name = name;
             request.version = version;
             request.description = description;

             if (resource) {
                 request.content = resource;
             } else if (link) {
                 request.link = link;
             } else {
                 MessageManager.showMessage('Error', 'You do not have added a resource');
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

        $('#upload').on('change', handleResourceSelection);
        $('.modal-footer > .btn').click(makeRegisterResRequest);
    };

})();
