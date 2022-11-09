odoo.define('azbah_pos.customer_fields', function (require) {
    "User strict";
    console.log("Hi Ehab!")
    let models = require('point_of_sale.models');
    models.load_fields("res.partner", ["code", "english_name"]);
});