odoo.define('bi_pos_restrict_zero_qty.productScreen', function(require) {
    "use strict";

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc')

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
                var config_id=self.env.pos.config.id;
                let prod_used_qty = {};

                // List of product IDs that are exempt from zero quantity restriction
                const exempted_product_ids = [3562, 37, 38];

                if(pos_config.restrict_zero_qty){
                    for (let line of lines) {
                        let prd = line.product;

                        // Skip the check for exempted products
                        if (exempted_product_ids.includes(prd.id)) {
                            continue;
                        }

                        let prd_qty_available = await this.rpc({
                            model: 'product.product',
                            method: 'get_qty_in_location',
                            context: {current_pos_config_id: config_id},
                            args: [prd.id, config_id],
                        });
                        if (prd.type == 'product'){
                            if(prd.id in prod_used_qty){
                                let old_qty = prod_used_qty[prd.id][1];
                                prod_used_qty[prd.id] = [prd_qty_available,line.quantity+old_qty]
                            }else{
                                prod_used_qty[prd.id] = [prd_qty_available,line.quantity]
                            }
                        }
                        if(prd_qty_available <= 0){
                            if (prd.type == 'product'){
                                call_super = false;
                                let wrning = prd.display_name + ' is out of stock.';
                                self.showPopup('ErrorPopup', {
                                    title: self.env._t('Zero Quantity Not allowed'),
                                    body: self.env._t(wrning),
                                });
                            }
                        }
                    }

                    $.each(prod_used_qty, function( i, pq ){
                        let product = self.env.pos.db.get_product_by_id(i);
                        let check = pq[0] - pq[1];
                        let wrning = product.display_name + ' is out of stock.';

                        // Skip the check for exempted products
                        if (exempted_product_ids.includes(product.id)) {
                            return true; // continue the $.each loop
                        }

                        if (product.type == 'product'){
                            if (check < 0){
                                call_super = false;
                                self.showPopup('ErrorPopup', {
                                    title: self.env._t('Deny Order'),
                                    body: self.env._t(wrning),
                                });
                            }
                        }
                    });

                }
                if(call_super){
                    super._onClickPay();
                }
            }
        };

    Registries.Component.extend(ProductScreen, BiProductScreen);

    return ProductScreen;

});
