odoo.define('azbah_pos.serials', function (require) {
    "use strict";

    let models = require('point_of_sale.models');
    let _super_orderline = models.Orderline.prototype;

    models.Orderline = models.Orderline.extend({
        set_quantity: function (quantity, keep_price) {

            // Call the original method
            let result = _super_orderline.set_quantity.apply(this, [quantity, keep_price]);

            this.update_serials(this.pack_lot_lines, this.quantity);
            return result;

        },
        update_serials: function (packlot, qty) {
            if (qty !== '' && packlot.length > 0) {

                let orderline = this;//.env.pos.get_order().get_selected_orderline()
                let first_serial = orderline.pack_lot_lines.models[0].attributes["lot_name"]
                first_serial = parseInt(first_serial)
                let newPackLotLines = [];
                for (let i = 0; i < parseInt(qty); i++) {
                    newPackLotLines.push(
                        {
                            "lot_name": (first_serial + i).toString(),
                        }
                    )
                }

                let draftPackLotLines = {
                    modifiedPackLotLines: {},
                    newPackLotLines: newPackLotLines
                }

                if (parseInt(qty) != parseInt(packlot.length))
                    orderline.setPackLotLines(draftPackLotLines);

            }
        }

    });
});


