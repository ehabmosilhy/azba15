odoo.define('ejad_erp_helpdesk.sub_type_ticket', function (require) {

    "use strict";
    console.log("subticket type file Loaded")
    // Odoo class to calling an url with JSONRPC
    var ajax = require('web.ajax');

        $('#ticket_type_id').change(function(){
            ajax.jsonRpc("/subtickettype", 'call', {'ticket_type_id': $(this).val()})
            .then(function (data) {
                  // Action after update
                  var part1 = ' <label class="col-form-label" for="ticket_type_line_id">Sub Type</label> <select type="text" class="form-control o_website_form_input" id="ticket_type_line_id" name="ticket_type_line_id" required="1">'
                  var html = "";
                  for(var x in data){
                    var obj = data[x]
                    for(var key in obj){
                        html += "<option value="+ key + ">" + obj[key] + "</option>"
                    }
                  }
                  var part2 = '</select>'
                  if (data.length){
                    document.getElementById("ticket_type_line_div").innerHTML = part1 + html + part2;
                  }
                  else{
                    document.getElementById("ticket_type_line_div").innerHTML = " ";
                  }
             });
       });
//       for if no ticket with this id in query ticket form
//
//        $('#submit_btn_ticket_id').click(function (e) {
//        e.preventDefault();
////        alert("Clicked")
//        ajax.jsonRpc('/check_ticket_exist', 'call', {'ticket_id': $('#query_ticket_id').val()})
//            .then(function (result) {
//                if (result){
//                    console.log("There are A Ticket")
//                    window.location.replace("/helpdesk/ticket_status");
//                }
//                else
//                {
//                    alert("No Ticket with this number")
////                      console.log("Noooooooo ")
//                }
//            });
//
//        });
    });