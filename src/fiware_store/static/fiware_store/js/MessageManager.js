
(function () {
    MessageManager = {};

    MessageManager.showMessage = function showMessage(title, msg) {

        $('#message-container').empty();
        $.template('modal', $('#modal_template'));
        $.tmpl('modal', {'title': title, 'message': msg}).appendTo('#message-container');

        $('#message').modal('show');
        $('#message').on('hidden', function() {
            $('#message-container').empty();
        });
    };

    MessageManager.showAlertError = function showAlertError(title, msg) {
        
        $('#message-container').empty();
        $.template('alertError', $('#alert_error_template'));
        $.tmpl('alertError', {'title': title, 'message': msg}).appendTo('#message-container');

        $('#message').bind('closed', function() {
            $('#message-container').empty();
        });
    };

    MessageManager.showAlertInfo = function showAlertInfo(title, msg) {
        
        $('#message-container').empty();
        $.template('alertInfo', $('#alert_info_template'));
        $.tmpl('alertInfo', {'title': title, 'message': msg}).appendTo('#message-container');

        $('#message').bind('closed', function() {
            $('#message-container').empty();
        });
    };

})();
