odoo.define('bi_pos_restrict_zero_qty.productScreen', function(require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
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
                if(pos_config.restrict_zero_qty){
                    for (let line of lines) {
                        let prd = line.product;
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



odoo.define('bi_pos_restrict_zero_qty.ProductItem', function(require) {
    'use strict';

    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');
    const { useExternalListener } = owl.hooks;

    const MyProductItem = (ProductItem) =>
        class extends ProductItem {
            constructor() {
                super(...arguments);
                useExternalListener(window, 'update-product-qty', this.updateProductQty);
            }
            mounted() {
                super.mounted();
                this.env.pos.on('change:selectedOrder', this.updateProductQty, this);
            }
            willUnmount() {
                super.willUnmount();
                this.env.pos.off('change:selectedOrder', this.updateProductQty, this);
            }
            async updateProductQty() {
                let product = this.props.product;
                let pos_config_id = this.env.pos.config.id;
                let qty = await this.rpc({
                    model: 'product.product',
                    method: 'get_qty_in_location',
                    args: [product.id, pos_config_id],
                });
                product.qty_available = qty;
            }
        };

    Registries.Component.extend(ProductItem, MyProductItem);

    return MyProductItem;
});
