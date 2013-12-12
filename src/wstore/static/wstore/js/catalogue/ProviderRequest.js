(function() {

    /**
     * Constructor for provider requests modal form
     * @param userProfile object with the user info
     * @returns {ProviderRequestForm}
     */
    ProviderRequestForm = function ProviderRequestForm(userProfile) {
        this.userProfile = userProfile
    };

    /**
     * ProviderRequestForm is a subclass of ModalForm
     */
    ProviderRequestForm.prototype = new ModalForm('Become a provider', '#provider_request_template');

    ProviderRequestForm.prototype.constuctor = ProviderRequestForm;

    /**
     * Makes the user request
     */
    ProviderRequestForm.prototype.makeProviderRequest = function makeProviderRequest() {
        var csrfToken = $.cookie('csrftoken');
        var request = {
            'username': this.userProfile.getUsername(),
        }

        if ($.trim($('#msg').val()) != '') {
            request.message =$.trim($('#msg').val())
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "POST",
                url: EndpointManager.getEndpoint('REQUEST_PROVIDER'),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: (function (response) {
                    $('#message').modal('hide');
                    this.userProfile.providerRequest = true;
                    $('#become-prov').val('Request pending');
                    MessageManager.showMessage('Sent', 'Your request has been sent');
                }).bind(this),
                error: (function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    this.modalCreated = false;
                    MessageManager.showMessage('Error', msg);
                }).bind(this)
            });
        } else {
            $('#alert-container').empty();
            MessageManager.showAlertError('Error', 'The message field is required', $('#alert-container'));
        }
    };

    /**
     * Implementation of the method defined in ModalForm
     */
    ProviderRequestForm.prototype.includeContents = function includeContents() {
        var msg = 'A request will be sent to a WStore admin in order to give you the Offering Provider role'

        // Append the informative message
        MessageManager.showAlertInfo('Note', msg, $('#alert-container'));
    };

    /**
     * Implementation of the method defined in ModalForm
     */
    ProviderRequestForm.prototype.setListeners = function setListeners() {
     // Set the hidden listeners
        $('#message').on('hidden', (function() {
            this.modalCreated = false;
        }).bind(this));

        // Set the button listener
        $('.modal-footer .btn').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.makeProviderRequest()
        }).bind(this));
    };
})();