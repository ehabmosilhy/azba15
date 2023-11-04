odoo.define('az_ks_pos_low_stock_alert.ks_low_stock', function (require) {
    "use strict";

    let ks_models = require('point_of_sale.models');
    const KsPaymentScreen = require('point_of_sale.PaymentScreen');
    const ks_utils = require('az_ks_pos_low_stock_alert.utils');
    const Registries = require('point_of_sale.Registries');

    ks_models.load_fields('product.product', ['type', 'qty_available']);
    let ks_super_pos = ks_models.PosModel.prototype;

    ks_models.PosModel = ks_models.PosModel.extend({
        initialize: function (session, attributes) {
            this.ks_load_product_quantity_after_product();
            ks_super_pos.initialize.call(this, session, attributes);
        },


        ks_get_model_reference: function (ks_model_name) {
            let ks_model_index = this.models.map(function (e) {
                return e.model;
            }).indexOf(ks_model_name);
            if (ks_model_index > -1) {
                return this.models[ks_model_index];
            }
            return false;
        },

        ks_load_product_quantity_after_product: function () {
            let ks_product_model = this.ks_get_model_reference('product.product');
            let ks_product_super_loaded = ks_product_model.loaded;
            ks_product_model.loaded = (self, ks_products) => {

                /*
                #  /\_/\
                # ( ◕‿◕ )
                #  >   <
                # Get the prdoduct qty in the location
                 */
                ks_products.forEach(ks_product => {
                    this.rpc({
                        model: 'product.product',
                        method: 'get_qty_in_location',
                        args: [ks_product.id, self.env.pos.config.id],
                    }).then(function (qty) {
                        self.db.qty_by_product_id[ks_product.id] = qty;
                    })
                });
                // ______ (｡◔‿◔｡) ________ End of code


                let done = $.Deferred();
                if (!self.config.allow_order_when_product_out_of_stock) {
                    let ks_blocked_product_ids = [];
                    for (let i = 0; i < ks_products.length; i++) {
                        if (ks_products[i].qty_available <= 0 && ks_products[i].type == 'product') {
                            ks_blocked_product_ids.push(ks_products[i].id);
                        }
                    }
                    let ks_blocked_products = ks_products.filter(function (p, index, arr) {
                        return ks_blocked_product_ids.includes(p.id);
                    });
                    ks_products = ks_products.concat(ks_blocked_products);
                }

                ks_product_super_loaded(self, ks_products);
                self.ks_update_qty_by_product_id(self, ks_products);
                done.resolve();
            }
        },

        ks_update_qty_by_product_id(self, ks_products) {
            if (!self.db.qty_by_product_id) {
                self.db.qty_by_product_id = {};
            }
            ks_products.forEach(ks_product => {
                self.db.qty_by_product_id[ks_product.id] = ks_product.qty_available;
            });
            self.ks_update_qty_on_product();
        },

        ks_update_qty_on_product: function () {
            let self = this;
            let ks_products = self.db.product_by_id;
            let ks_product_quants = self.db.qty_by_product_id;
            for (let pro_id in self.db.qty_by_product_id) {
                ks_products[pro_id].qty_available = ks_product_quants[pro_id];
            }
        },

        push_single_order: function (ks_order, opts) {
            let ks_pushed = ks_super_pos.push_single_order.call(this, ks_order, opts);
            if (ks_order) {
                this.ks_update_product_qty_from_order(ks_order);
            }
            return ks_pushed;
        },

        ks_update_product_qty_from_order: function (ks_order) {
            let self = this;
            ks_order.orderlines.forEach(line => {
                let ks_product = line.get_product();
                if (ks_product.type == 'product') {
                    ks_product.qty_available -= line.get_quantity();
                    self.ks_update_qty_by_product_id(self, [ks_product]);
                }
            });
        }
    });

    // overriding the existing class to validate the payment order
    /*
    const ks_payment = (KsPaymentScreen) =>
        class extends KsPaymentScreen {

            async validateOrder(isForceValidate) {
                if (await this._isOrderValid(isForceValidate) && ks_utils.ks_validate_order_items_availability(this.env.pos.get_order(), this.env.pos.config)) {
                    // remove pending payments before finalizing the validation
                    for (let line of this.paymentLines) {
                        if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                    }
                    await this._finalizeValidation();
                }
            }
        };

    Registries.Component.extend(KsPaymentScreen, ks_payment);

    return KsPaymentScreen;

     */
});