(function() {

    ProviderRequestForm = function ProviderRequestForm(userProfile) {
        this.modalDisplayed = false;
        this.userProfile = userProfile
    };

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
                    this.modalDisplayed = false;
                    MessageManager.showMessage('Error', msg);
                }).bind(this)
            });
        } else {
            $('#alert-container').empty();
            MessageManager.showAlertError('Error', 'The message field is required', $('#alert-container'));
        }
    };

    ProviderRequestForm.prototype.display = function display() {
        var msg = 'A request will be sent to a WStore admin in order to give you the Offering Provider role'

        // Create the modal if it is not displayed
        if(!this.modalDisplayed) {
            MessageManager.showMessage('Become a provider', '');
            this.modalDisplayed = true;
        }
        $('.modal-body').empty();

        // Append the informative message
        $('<div></div>').attr('id', 'alert-container').appendTo('.modal-body');
        MessageManager.showAlertInfo('Note', msg, $('#alert-container'));

        $('<div></div>').addClass('space clear').appendTo('.modal-body');
        $('<p></p>').text('Write a message').appendTo('.modal-body');
        $('<textarea></textarea>').attr('id', 'msg').addClass('span8').css('height', '100px').appendTo('.modal-body');

        // Set the hidden listeners
        $('#message').on('hidden', (function() {
            this.modalDisplayed = false;
        }).bind(this));

        // Set the button listener
        $('.modal-footer .btn').click((function(evnt) {
            evnt.preventDefault();
            evnt.stopPropagation();
            this.makeProviderRequest()
        }).bind(this));
    };
})();