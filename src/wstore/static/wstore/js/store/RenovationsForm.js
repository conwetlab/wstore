
(function(){
    var makeRenovationRequest = function makeRenovationRequest(offElem) {
        var request, error = false;
        var msg;
        var csrfToken = $.cookie('csrftoken');
        var ref = offElem.bill[0].split('_')[0];

        ref = ref.split('/')[3];

        // Add payment info
        request = {};
        if ($('#pay-method').val() == 'credit_card') {
            var cvv2 = $.trim($('#cvv2').val());

            request.method = 'credit_card';

            if (!$('curr-card').prop('checked')) {
                var number, year;

                number = $.trim($('#number').val());
                year = $.trim($('#expire-year').val());

                if (!(number == '') && !(year == '') && !(cvv2 == '')) {
                    request.credit_card = {
                        'number': number,
                        'type': $('#type').val(),
                        'expire_month': $('#expire-month').val(),
                        'expire_year': year,
                        'cvv2': cvv2
                    }
                } else {
                    error = true;
                    msg = 'Missing required field';
                }
            }
        } else {
            request.method = 'paypal';
        }

        if (!error) {
            $.ajax({
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                type: "PUT",
                url: EndpointManager.getEndpoint('PURCHASE_ENTRY', {
                    'ref': ref
                }),
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify(request),
                success: function (response) {
                    $('#message').modal('hide');
                    MessageManager.showMessage('Renovated', 'Subscriptions has been renovated');
                    refreshAndUpdateDetailsView();
                },
                error: function (xhr) {
                    var resp = xhr.responseText;
                    var msg = JSON.parse(resp).message;
                    $('#message').modal('hide');
                    MessageManager.showMessage('Error', msg);
                }
            });
        } else {
            MessageManager.showAlertError('Error', msg, $('#purchase-error'));
        }
    };

    var showPaymentForm = function showPaymentForm(offElem) {
        var select, acceptButton, cancelButton;
        // Crear modal body
        $('.modal-body').empty();

        $('<div></div>').attr('id', 'purchase-error').appendTo('.modal-body');
        $('<div></div>').addClass('space clear').appendTo('.modal-body');

        // Append select component to choose payment method
        $('<p></p>').text('Payment method').appendTo('.modal-body');
        select = $('<select></select>').attr('id', 'pay-method').appendTo('.modal-body');
        $('<option></option>').text('------').appendTo(select);
        $('<option></option>').val('credit_card').text('Credit card').appendTo(select);
        $('<option></option>').val('paypal').text('Paypal').appendTo(select);
        
        $('<div></div>').attr('id', 'method-cont').appendTo('.modal-body');
        $('#pay-method').change(function() {
            // In case the payment method were credit card, append credit card form
            if ($('#pay-method').val() == 'credit_card') {
                var checked = false;
                
                $('<label></label>').attr('for', 'curr-card').text('Use user profile credit card').appendTo('#method-cont');
                $('<input></input>').attr('type', 'checkbox').attr('value', 'curr-card').attr('id', 'curr-card').appendTo('#method-cont');
                $('<div></div>').attr('id', 'card-form').appendTo('#method-cont');
                
                $.template('CreditCardTemplate', $('#credit_card_template'));
                $.tmpl('CreditCardTemplate', {}).appendTo('#card-form');

                // If the user uses their user profile credit card only the cvv2 code 
                // is needed
                $('#curr-card').change(function() {
                    if (checked) {
                        $('#card-form').empty();
                        $.template('CreditCardTemplate', $('#credit_card_template'));
                        $.tmpl('CreditCardTemplate', {}).appendTo('#card-form');
                        checked = false
                    } else {
                        $('#card-form').empty();
                        checked = true;
                    }
                })
            } else {
                $('#method-cont').empty();
            }
        });

        $('.modal-footer').empty();
        acceptButton = $('<button></button>').attr('class', 'btn btn-basic').appendTo('.modal-footer');
        acceptButton.text('Accept');

        acceptButton.click(function(evnt) {
            evnt.preventDefault();
            makeRenovationRequest(offElem);
        });

        cancelButton = $('<button></button>').attr('class', 'btn btn-danger').text('Cancel');
        cancelButton.appendTo('.modal-footer');
        cancelButton.click(function() {
            $('#message').modal('hide');
        })
    }

    paintRenovationForm = function paintRenovationForm(outDated, offElem) {
        var btnYes, btnNo;
        var msg = 'Pending renovations';
        MessageManager.showMessage(msg, 'The following subscriptions are out of date: ');
        for (var i = 0; i < outDated.length; i++) {
            var p = $('<p></p>');
            $('<b></b>').text(outDated[i].title).appendTo(p);
            p.appendTo('.modal-body');
            $('<p></p>').text('Price: ' + outDated[i].value + ' ' + outDated[i].currency + ' ' + outDated[i].unit).appendTo('.modal-body');
        }
        $('<div></div>').attr('class', 'line clear').appendTo('.modal-body');
        $('<p></p>').text('Do you want to renovate them?').appendTo('.modal-body');

        $('.modal-footer').empty();
        btnYes = $('<button></button>').text('Yes').attr('class', 'btn btn-basic');
        btnYes.appendTo('.modal-footer');
        btnYes.click(function() {
           showPaymentForm(offElem);
        });

        btnNo = $('<button></button>').text('No').attr('class', 'btn btn-danger');
        btnNo.appendTo('.modal-footer');
        btnNo.click(function() {
            $('#message').modal('hide');
        });
    };
})();