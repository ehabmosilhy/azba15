odoo.define('ejad_erp_auth_oauth.ejad_sms_login', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    $(document).ready(function() {

        $("#login").focus();

        $("#login").blur(function(){
            $('.messages').remove();
            $('#wk_error').remove();
            var login = $('#login').val();
            ajax.jsonRpc("/check/mobile", 'call', {'login': login})
            .then(function (data) {
                 if (data[2] == 1) {
                    $('.btn.btn-primary.btn-block').parent().hide();
                    if (data[0] == 'mobile') {
                        $("#nextBtnDiv2").hide();
                        $("#nextBtnDiv").show();
                    } else {
                        $('.btn.btn-primary.btn-block').parent().show();
                        $("#nextBtnDiv").hide();
                    }
                 }
                  else {
                    console.log(data)
                }
            });
        });

        $('.wk_next_btn').on('click', function(e) {
            var recaptcha = $("#g-recaptcha-response").val();
            if (recaptcha === "") {
                event.preventDefault();
                document.getElementById('err').innerHTML= _t("Please verify Captcha");
            }
            else{
                $('#wk_error').remove();
                generateLoginSms();
            }

        });

        $("#nextBtn2").on('click', function(e) {
            $('#wk_error').remove();
            var sms_code = $('#codeSms').val();

            ajax.jsonRpc("/verify/sms", 'call', {'sms_code': sms_code})
            .then(function (data) {
                 if (data[0] == 7){
                    $(".field-otp-option").after("<p id='wk_error' class='alert alert-danger'>" + data[1] + "</p>");
                    $('#codeSms').val('');
                } else {
                    $(".oe_login_form").submit();
                }
            });
        });

        $(this).on('click', '.wk_login_resend', function(e) {
            generateLoginSms();
            $('.wk_login_resend').remove();
        });

    });

    function generateLoginSms() {
        var login = $('#login').val();
        var password = $('#password').val();

        ajax.jsonRpc("/send/sms", 'call', {'login': login, 'password': password})
            .then(function (data) {
                if (data[0] == 0) {
                    $("#password").parent().after("<p id='wk_error' class='alert alert-danger'>" +data[1] + "</p>");
                }else{
                    $("#login").prop('readonly', true);
                    $("#password").prop('readonly', true);
                     $("a.btn-link").hide();
                    $(".field-otp-option").css("display","");
                    $('.wk_next_btn').parent().hide();
                    $("#nextBtnDiv2").show();

                    $('#wk_error').remove();
                    getLoginInterval(data[2]);
                }
            });
    };

    function getLoginInterval(otpTimeLimit) {
        var countDown = otpTimeLimit;
        var x = setInterval(function() {
            countDown = countDown - 1;
            $("#otplogincounter").html("رمز التثبت تنتهي صلاحيته خلال " + countDown + " ثانية.");
            if (countDown < 0) {
                clearInterval(x);
                $('#wk_error').remove();
                $("#otplogincounter").html("<p><a class='btn btn-link pull-right wk_login_resend' href='#'>إعادة إرسال رمز للتثبت</a></p>");
            }
        }, 1000);
    }
})