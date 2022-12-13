odoo.define('azbah_pos.invoice_number', function (require) {
    "use strict"

    let model = require("point_of_sale.models");
    let SuperPosModel = model.PosModel.prototype;
    let SuperOrder = model.Order.prototype;
    let rpc = require('web.rpc');
    let _super_order = model.Order.prototype;



    model.PosModel = model.PosModel.extend({
        _flush_orders: function (orders, options) {
            let self = this;
            let result, data
            result = data = SuperPosModel._flush_orders.call(this, orders, options)
            _.each(orders, function (order) {
                if (order.to_invoice)
                    data.then(function (order_server_id) {
                        rpc.query({
                            model: 'pos.order',
                            method: 'read',
                            args: [order_server_id, ['account_move']]
                        }).then(function (result_dict) {
                            if (result_dict.length) {
                                // let invoice = result_dict[0].account_move;
                                // self.get_order().invoice_number = invoice[1]

                                let invoice = result_dict[0].account_move;
                                let order_id = result_dict[0].id;

                                self.get_order().invoice_number = invoice[1]
                                self.get_order().id = order_id
                            }
                        })
                            .catch(function (error) {
                                return result
                            })
                    })
            })
            return result
        },
    })
    model.Order = model.Order.extend({
        export_for_printing: function () {
            let self = this
            let receipt = SuperOrder.export_for_printing.call(this)
            if (self.invoice_number) {
                receipt.invoice_number = self.invoice_number.split(" ")[0];
                receipt.id = self.id;
            }
            return receipt
        }
    })
    model.Order = model.Order.extend({

        // Ehab
        get_invoice_name: function () {
            return this.invoice_name;
             },

        //Ebrahiem
        export_for_printing: function () {
            var order = this.pos.get_order();
            var json = _super_order.export_for_printing.apply(this, arguments);
            if (this.invoice_name) {
                json.invoice_name = this.invoice_name;
            } else {
                json.invoice_name = ""
            }

            console.log("_super_order", this)
            return json;
        },
    });
})


