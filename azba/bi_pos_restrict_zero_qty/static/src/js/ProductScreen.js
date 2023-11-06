// BiProductScreen js
odoo.define('bi_pos_restrict_zero_qty.productScreen', function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var rpc = require('web.rpc')

    /*
   #  /\_/\
   # ( ◕‿◕ )
   #  >   <
   # Get the prdoduct qty in the location
    */
    let models = require('point_of_sale.models');
    let _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({


        initialize: function (session, attributes) {
            let self = this;
            let product_model = _.find(this.models, function (model) {
                return model.model === 'product.product';
            });

            if (product_model) {
                let _super_loaded = product_model.loaded;
                product_model.loaded = function (self, products) {
                    _super_loaded(self, products);

                    // this should be a function
                    if (!self.db.qty_by_product_id) {
                        self.db.qty_by_product_id = {};
                    }
                    products.forEach(ks_product => {
                        self.db.qty_by_product_id[ks_product.id] = ks_product.qty_available;
                    });


                    products.forEach(product => {
                        self.rpc({
                            model: 'product.product',
                            method: 'get_qty_in_location',
                            args: [product.id, self.config.id],
                        }).then(function (qty) {
                            self.db.qty_by_product_id[product.id] = qty;
                        });
                    });
                };
            }

            return _super_posmodel.initialize.call(this, session, attributes);
        },
    });

    // ______ (｡◔‿◔｡) ________ End of code
    const BiProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
            }

            async _onClickPay() {
                var self = this;
                let order = this.env.pos.get_order();
                let lines = order.get_orderlines();
                let pos_config = self.env.pos.config;
                let call_super = true;
                var config_id = self.env.pos.config.id;
                let prod_used_qty = {};
                if (pos_config.restrict_zero_qty) {
                    $.each(lines, function (i, line) {
                        let prd = line.product;
                        if (prd.type == 'product') {
                            if (prd.id in prod_used_qty) {
                                let old_qty = prod_used_qty[prd.id][1];
                                prod_used_qty[prd.id] = [prd.qty_available, line.quantity + old_qty]
                            } else {
                                prod_used_qty[prd.id] = [prd.qty_available, line.quantity]
                            }
                        }
                        if (prd.qty_available <= 0) {
                            if (prd.type == 'product') {
                                call_super = false;
                                let wrning = prd.display_name + ' is out of stock.';
                                self.showPopup('ErrorPopup', {
                                    title: self.env._t('Zero Quantity Not allowed'),
                                    body: self.env._t(wrning),
                                });
                            }
                        }
                    });

                    $.each(prod_used_qty, function (i, pq) {
                        let product = self.env.pos.db.get_product_by_id(i);
                        let check = pq[0] - pq[1];
                        let wrning = product.display_name + ' is out of stock.';
                        if (product.type == 'product') {
                            if (check < 0) {
                                call_super = false;
                                self.showPopup('ErrorPopup', {
                                    title: self.env._t('Deny Order'),
                                    body: self.env._t(wrning),
                                });
                            }
                        }
                    });

                }
                if (call_super) {
                    super._onClickPay();
                }
            }
        };

    Registries.Component.extend(ProductScreen, BiProductScreen);

    return ProductScreen;

});
