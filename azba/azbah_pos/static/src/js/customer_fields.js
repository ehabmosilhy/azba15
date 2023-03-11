odoo.define('azbah_pos.customer_fields', function (require) {
    "User strict";
    let models = require('point_of_sale.models');
    var _super_product = models.PosModel.prototype;
    models.load_fields("res.partner", ["code", "english_name"]);
    models.load_fields("pos.order", ["id", "invoice_id","invoice_name"]);
//
// models.PosModel = models.PosModel.extend({
//         initialize: function(session, attributes){
//             var self = this;
//             models.load_fields('pos.order', ['invoice_name']);
//             _super_product.initialize.apply(this, arguments);
//         }
//     });
// });
//
// odoo.define('azbah_pos.receipt', function(require){
//     "use strict";
//     var models = require('point_of_sale.models');
//     models.load_fields('pos.order', 'invoice_name');
//     var _super_order = models.Order.prototype;
//     models.Order = models.Order.extend({
//         export_for_printing: function(){
//             var order = _super_order.export_for_printing.apply(this, arguments);
//             order.invoice_name = this.invoice_name;
//             return order;
//         }
//     });
});
