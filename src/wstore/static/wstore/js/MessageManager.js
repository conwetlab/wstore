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
    MessageManager = {};

    MessageManager.showMessage = function showMessage(title, msg, msgContainer) {
        var container = $('#message-container');
        var id = 'message';

        if (msgContainer) {
            container = msgContainer;
            id = 'sec-message';
        }
        container.empty();
        $.template('modal', $('#modal_template'));
        $.tmpl('modal', {
            'title': title,
            'message': msg,
            'id': id
        }).appendTo(container);

        $('#' + id).modal('show');
        $('#' + id).on('hidden', function() {
            container.empty();
        });
    };

    var showAlert = function(title, msg, template, messageCont) {
        var container = $('#message-container');

        if (messageCont) {
            container = messageCont;
        }

        container.empty();
        $.template('alert', template);
        $.tmpl('alert', {'title': title, 'message': msg}).appendTo(container);

        $('#message').bind('closed', function() {
            $(container).empty();
        });
    };

    MessageManager.showAlertError = function showAlertError(title, msg, messageCont) {
        showAlert(title, msg, $('#alert_error_template'), messageCont);
    };

    MessageManager.showAlertInfo = function showAlertInfo(title, msg, messageCont) {
        showAlert(title, msg, $('#alert_info_template'), messageCont);
    };

    MessageManager.showAlertWarning = function showAlertWarning(title, msg, messageCont) {
        showAlert(title, msg, $('#alert_warning_template'), messageCont);
    };

    MessageManager.showYesNoWindow = function showYesNoWindow (msg, handler, tit, msgContainer, cancelHandler) {
        var title = '';
        var container = $('#message-container');
        var id = 'message';

        // Default cancel behaviour is closing the window 
        var cHandler = function  () {
            $('#' + id).modal('hide');
        };

        if (tit) {
            title = tit;
            if (msgContainer) {
                container = msgContainer;
                id = 'sec-message';

                if (cancelHandler) {
                    cHandler = cancelHandler;
                }
            }
        }

        container.empty();
        $.template('yesNoWindowTemplate', $('#yes_no_window_template'));
        $.tmpl('yesNoWindowTemplate', {
            'title': tit,
            'msg': msg,
            'id': id
        }).appendTo(container);

        $('#btn-yes').click(function() {
            $('#' + id).modal('hide');
            handler();
        });

        $('#btn-no').click(cHandler);

        $('#' + id).modal('show');
        $('#' + id).on('hidden', function() {
            cHandler();
            container.empty();
        })
    }

})();
