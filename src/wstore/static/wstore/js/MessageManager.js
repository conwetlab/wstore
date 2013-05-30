
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

    MessageManager.showAlertError = function showAlertError(title, msg, messageCont) {
        var container = $('#message-container');

        if (messageCont) {
            container = messageCont;
        }

        container.empty();
        $.template('alertError', $('#alert_error_template'));
        $.tmpl('alertError', {'title': title, 'message': msg}).appendTo(container);

        $('#message').bind('closed', function() {
            $(container).empty();
        });
    };

    MessageManager.showAlertInfo = function showAlertInfo(title, msg, messageCont) {
        var container = $('#message-container');
        var template;

        if (messageCont) {
            container = messageCont;
        }

        container.empty();
        $.template('alertInfo', $('#alert_info_template'));
        template = $.tmpl('alertInfo', {'title': title, 'message': msg})
        container.append(template);

        $('#message').bind('closed', function() {
            $(container).empty();
        });
    };

    MessageManager.showYesNoWindow = function showYesNoWindow (msg, handler, tit) {
        var title = '';

        if (tit) {
            title = tit;
        }

        $('#message-container').empty();
        $.template('yesNoWindowTemplate', $('#yes_no_window_template'));
        $.tmpl('yesNoWindowTemplate', {
            'title': tit,
            'msg': msg
        }).appendTo('#message-container');

        $('#btn-yes').click(handler);
        $('#btn-no').click(function  () {
            $('#message').modal('hide');
        });

        $('#message').modal('show');
        $('#message').on('hidden', function() {
            $('#message-container').empty();
        })
    }

})();
