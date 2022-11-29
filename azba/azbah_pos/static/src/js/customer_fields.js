odoo.define('azbah_pos.customer_fields', function (require) {
    "User strict";
    let models = require('point_of_sale.models');

    models.load_fields("res.partner", ["code", "english_name"]);
    models.load_fields("pos.order", ["id"]);
})
    // var super_order_model = models.Order.prototype;
    // models.Order = models.Order.extend({
    //     initialize: function (attributes, options) {
    //         super_order_model.initialize.apply(this, arguments);
    //         if (!options.json) {
    //             this.employee = this.pos.get_cashier();
    //         }
    //     }});