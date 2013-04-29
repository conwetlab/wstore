(function() {

    var userDisplayed;
    var addrDisplayed;
    var paymentDisplayed;

    var paintUserConf = function painUserConf(userInfo) {
        var taxAddr, paymentInfo;

        userDisplayed = false;
        addrDisplayed = false;
        paymentDisplayed = false;

        MessageManager.showMessage('Configuration', '');
        $.template('userConfTemplate', $('#user_conf_template'));
        $.tmpl('userConfTemplate').appendTo('.modal-body');

        // Paint user info
        paintUserInfo(userInfo);

        if (userInfo.tax_address) {
            taxAddr = userInfo.tax_address;
        } else {
            taxAddr = false;
        }

        paintAddressInfo(taxAddr);

        if (userInfo.payment_info) {
            paymentInfo = userInfo.payment_info;
        } else {
            paymentInfo = false;
        }

        paintPaymentInfo(paymentInfo);
    };

    var paintUserInfo = function paintUserInfo(userInfo) {
        if (!userDisplayed) {
            userDisplayed = true;
            // Load the user info
            context = {
                'username': userInfo.username,
                'first_name': userInfo.first_name,
                'last_name': userInfo.last_name,
                'organization': userInfo.organization
            }

            $.template('userInfoConfTemplate', $('#user_info_conf_template'));
            $.tmpl('userInfoConfTemplate', context).appendTo('#userinfo-tab');

            // Set an edit button
            // Set listeners
        }
    };

    var paintAddressInfo = function paintAddressInfo(taxAddr) {
        if(!addrDisplayed) {
            addrDisplayed = true;
            context = {
                'street': taxAddr.street,
                'postal': taxAddr.postal,
                'city': taxAddr.city,
                'country': taxAddr.country
            }

            $.template('addressConfTemplate', $('#address_conf_template'));
            $.tmpl('addressConfTemplate', context).appendTo('#taxaddr-tab');
        }
    };

    var paintPaymentInfo = function paintPaymentInfo(paymentInfo) {
        if (!paymentDisplayed) {
            paymentDisplayed = true;
            context = {
                'type': paymentInfo.type,
                'number': paymentInfo.number,
                'year': paymentInfo.expire_year,
                'month': paymentInfo.expire_month
            }

            $.template('paymentInfoConfTemplate', $('#payment_info_conf_template'));
            $.tmpl('paymentInfoConfTemplate', context).appendTo('#paymentinfo-tab');
        }
    };

    var getUserInfo = function getUserInfo() {
        $.ajax({
            type: "GET",
            url: EndpointManager.getEndpoint('USERPROFILE_ENTRY', {'username': USERNAME}),
            dataType: "json",
            success: function (response) {
                paintUserConf(response);
            },
            error: function (xhr) {
                var resp = xhr.responseText;
                var msg = JSON.parse(resp).message;
                MessageManager.showMessage('Error', msg);
            }
        })
    };

    $(document).ready(function() {
        $('#conf-link').click(getUserInfo);
    });
})();