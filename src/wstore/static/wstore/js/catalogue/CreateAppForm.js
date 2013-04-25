
(function () {

    var screenShots = [];
    var usdl;
    var logo = [];

    var handleImageFileSelection = function handleImageFileSelection(evnt, type) {
        var files = evnt.target.files;
        var imagesList = [];

        var reader = new FileReader();

        var readImages = function readImages(images) {

            if(images.length > 0) {
                var img = images.pop();

                if (img.type.match('image.*')) {
                    reader.onload = (function(file) {

                        return function(e) {
                            var binaryContent = e.target.result;
                            var encoded = btoa(binaryContent);
                            if (type == 'screenshots') {
                                screenShots.push({
                                    'name': file.name,
                                    'data': encoded
                                });
                            } else if (type == 'logo') {
                                logo.push({
                                    'name': file.name,
                                    'data': encoded
                                });
                            }
                            readImages(images);
                        };
                    })(img);
                    reader.readAsBinaryString(img);
                }
            }
        }
        for(var i=0, f; f = files[i]; i+=1){
            imagesList.push(f);
        }
        readImages(imagesList);
    };

    var handleUSDLFileSelection = function handleUSDLFileSelection(evnt) {
        var f = evnt.target.files[0];
        var reader = new FileReader();

        reader.onload = (function(file) {
            return function(e) {
                var type = file.type;
                if (!type) {
                    if (file.name.match(/\.n3/i)) {
                        type = "text/n3";
                    } else if (file.name.match(/\.ttl/i)) {
                        type = "text/turtle";
                    }

                }
                if (type == 'application/rdf+xml' || type == 'text/n3' || type == 'text/turtle') {
                    usdl = {
                        'content_type': type,
                        'data': e.target.result
                    };
                }
            };
        })(f);
        reader.readAsText(f);
    };

    var makeCreateAppRequest = function makeCreateAppRequest(evnt) {
        var name, version, rep, csrfToken, request = {};

        evnt.preventDefault();
        name = $.trim($('[name="app-name"]').val());
        version = $.trim($('[name="app-version"]').val());
        rep = $('#repositories').val();
        $('#message').modal('hide');
        $('#message-container').empty();

        if (name && version && logo && rep && usdl){

            csrfToken = $.cookie('csrftoken');
            request.name = name;
            request.version = version;
            request.image = logo[0];
            request.offering_description = usdl;
            request.repository = rep;

            if (screenShots) {
                request.related_images = screenShots;
            }

            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "POST",
                url: EndpointManager.getEndpoint('OFFERING_COLLECTION'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    MessageManager.showMessage('Created', 'The offering has been created')
                    if (getCurrentTab() == '#provided-tab') {
                        getUserOfferings('#provided-tab', paintProvidedOfferings, false);
                    }
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

    showCreateAppForm = function showCreateAppForm(repositories) {
        var i, repLength = repositories.length;

        screenShots = [];
        logo = [];

        if (repLength == 0) {
            var msg = 'No repositories registered';
            MessageManager.showMessage('Error', msg);
            return
        }
        // Creates the modal
        MessageManager.showMessage('Create new offering', '');

        // Creates the form
        $.template('formTemplate', $('#create_app_form_template'));
        $.tmpl('formTemplate', {}).appendTo('.modal-body');

        for(i=0; i<repLength; i+=1) {
            $.template('radioTemplate', $('#radio_template'));
            $.tmpl('radioTemplate', {
                'name': 'rep-radio',
                'id': 'rep-radio' + i,
                'value': repositories[i].name,
                'text': repositories[i].name}).appendTo('#repositories');
        }

        // Create the listeners
        $('#usdl-editor').click(function(event) {
            window.open('/usdleditor', 'USDL editor');
        });

        $('#img-logo').change(function(event) {
            handleImageFileSelection(event, 'logo');
        });

        $('#screen-shots').change(function(event) {
            handleImageFileSelection(event, 'screenshots');
        });

        $('#usdl-doc').change(function(event) {
            handleUSDLFileSelection(event);
        });

        $('.modal-footer > .btn').click(function(event) {
            makeCreateAppRequest(event);
        });
    };

})();

