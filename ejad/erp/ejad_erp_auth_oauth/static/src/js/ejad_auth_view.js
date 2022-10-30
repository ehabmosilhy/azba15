odoo.define('ejad_erp_auth_oauth.ejad_auth_view', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    $(document).ready(function() {
        $("#oe_auth_form").validate({
          rules: {
            totp_token: {
              maxlength: 6,
              minlength: 6,
              number: true,
            },
          },
          messages: {
            totp_token: {
              maxlength: "كود التحقق يجب أن يتكون من ستة أرقام فقط",
              minlength: "كود التحقق يجب أن يتكون من ستة أرقام فقط",
              number: "كود التحقق يجب أن يتكون من أرقام فقط",
            },
          }
        });

        var countDown = $("#otpTimeLimit").val();
        if(countDown > 0){
            var x = setInterval(function() {
            countDown = countDown - 1;
            $("#otplogincounter").html("رمز التحقق تنتهي صلاحيته خلال " + countDown + " ثانية.");
            if (countDown < 0) {
                clearInterval(x);
                $("#otplogincounter").html("<p><a class='btn btn-link pull-right wk_login_resend' href='#'>إعادة إرسال رمز التحقق</a></p>");
            }
        }, 1000);


        }

    $("#nextBtn").on('click', function(e) {
            var sms_code = $('#totp_token').val();

            ajax.jsonRpc("/verify/sms", 'call', {'sms_code': sms_code})
            .then(function (data) {
                 if (data[0] == 7){
                    $("#otplogincounter").html("<p id='wk_error' class='alert alert-danger'>" + data[1] + "</p>");
                    $('#totp_token').val('');
                } else {
                    $(".oe_auth_form").submit();
                }
            });
      });

    $(this).on('click', '.wk_login_resend', function(e) {
            generateLoginSms();
            $('.wk_login_resend').remove();
        });


    function generateLoginSms() {
        var userid = $('#userid').val();

        ajax.jsonRpc("/send/sms", 'call', {'userid': userid})
            .then(function (data) {
                if (data[0] == 2) {
                    var countDown = data[2];
                    if(countDown > 0){
                        var x = setInterval(function() {
                        countDown = countDown - 1;
                        $("#otplogincounter").html("رمز التحقق تنتهي صلاحيته خلال " + countDown + " ثانية.");
                        if (countDown < 0) {
                            clearInterval(x);
                            $("#otplogincounter").html("<p><a class='btn btn-link pull-right wk_login_resend' href='#'>إعادة إرسال رمز التحقق</a></p>");
                        }
                    }, 1000);
                    }
                    $('#otpTimeLimit').val(data[2]);
                }
            });
    }




    });




});