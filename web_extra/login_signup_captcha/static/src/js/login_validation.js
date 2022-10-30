odoo.define('login_signup_captcha.login_validation', function (require) {

    "use strict";
 var core = require('web.core');
 var _t = core._t;

$(document).ready(function () {
    $("form").submit(function(event) {
        var recaptcha = $("#g-recaptcha-response").val();
        if (recaptcha === "") {
            event.preventDefault();
            document.getElementById('err').innerHTML= _t("Please verify Captcha");
        }
        else{
            return true;
        }
     });

//     $('.list-group-item.list-group-item-action.py-2').click(function(event){
//        var recaptcha = $("#g-recaptcha-response").val();
//        if (recaptcha === "") {
//            event.preventDefault();
//            document.getElementById('err').innerHTML= _t("Please verify Captcha");
//        }
//        else{
//            return true;
//        }
//     });


});

});