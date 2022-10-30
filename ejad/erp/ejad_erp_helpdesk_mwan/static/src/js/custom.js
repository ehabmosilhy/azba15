odoo.define('ejad_erp_helpdesk_mwan.custom_mwan', function (require) {

    "use strict";
$(document).ready(function () {
    console.log("111111");
    $("#contactus_send_ticket").validate({
      rules: {
        partner_email: {
          required: true,
          email: true
        },
        mobile: {
          required: true,
          maxlength: 10,
          minlength: 10
        },
        personal_id: {
          maxlength: 10,
          minlength: 10
        },
        commercial_reg_no: {
          maxlength: 10,
          minlength: 10
        },
        description: {
          maxlength: 260
        },
        name: {
          maxlength: 260
        }
      },
      messages: {
        name: "Please specify your name",
        mobile: {
          maxlength: "رقم الجوال يجب أن يتكون من عشر أرقام فقط",
          minlength: "رقم الجوال يجب أن يتكون من عشر أرقام فقط",
        },
        personal_id: {
          maxlength: "رقم الهوية يجب أن يتكون من عشر أرقام فقط",
          minlength: "رقم الهوية يجب أن يتكون من عشر أرقام فقط",
        },
        commercial_reg_no: {
          maxlength: "رقم السجل التجارى يجب أن يتكون من عشر أرقام فقط",
          minlength: "رقم السجل التجارى يجب أن يتكون من عشر أرقام فقط",
        },
        description: {
          maxlength: "الوصف يجب ان لايتجاوز 260 حرف"
        },
        name: {
          maxlength: "الوصف يجب ان لايتجاوز 260 حرف"
        },
        partner_email: {
          email: "يرجى إدخال بريد إلكتروني صحيح"
        }
      }
    });
    $("#helpdesk_ticket_form").validate({
      rules: {
        description: {
          maxlength: 260
        },
      },
      messages: {
        description: {
          maxlength: "الوصف يجب ان لايتجاوز 260 حرف"
        }

      }
    });



});

});