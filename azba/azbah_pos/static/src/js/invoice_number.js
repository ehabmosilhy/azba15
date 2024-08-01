odoo.define('azbah_pos.invoice_number',function(require){
    "use strict"

    let model = require("point_of_sale.models");
    let SuperPosModel = model.PosModel.prototype;
    let SuperOrder = model.Order.prototype;
    let rpc = require('web.rpc');
    var field_utils = require('web.field_utils');

    model.PosModel = model.PosModel.extend({
        _flush_orders: function(orders, options) {
            let self = this;
            let result, data
            result = data = SuperPosModel._flush_orders.call(this,orders, options)
            _.each(orders,function(order){
                if (order.to_invoice)
                    data.then(function(order_server_id){
                        rpc.query({
                        model: 'pos.order',
                        method: 'read',
                        args:[order_server_id, ['account_move']]
                            }).then(function(result_dict){
                                if(result_dict.length){

                                    let invoice = result_dict[0].account_move;
                                    let order_id = result_dict[0].id;

                                    self.get_order().invoice_number = invoice[1]
                                    self.get_order().id = order_id
                                }
                        })
                        .catch(function(error){
                            return result
                        })
                    })
            })
            return result
        },
    })
    model.Order = model.Order.extend({
        init_from_JSON: function(json) {
            SuperOrder.init_from_JSON.apply(this, arguments);
            if(json.order_date) {
                this.order_date = json.order_date;
            }
            if(json.invoice_number) {
                this.invoice_number = json.invoice_number;
            }
        },

        export_for_printing: function(){
            let self = this
            let receipt = SuperOrder.export_for_printing.call(this)
            if(self.invoice_number){
                receipt.invoice_number = self.invoice_number.split(" ")[0];
                receipt.id = self.id;
            }
            if(! receipt.date.localestring && this.order_date  ){
                 receipt.date.localestring = field_utils.format.datetime(moment(this.order_date), {}, {timezone: false});
            }
            return receipt
        }
    })
    model.Order = model.Order.extend({

        // Ehab
        get_invoice_name: function () {
            alert(this.invoice_name);
            return this.invoice_name;
        },
    });
})
