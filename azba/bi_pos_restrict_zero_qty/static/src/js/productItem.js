odoo.define('bi_pos_restrict_zero_qty.ProductItem', function(require) {
    'use strict';

    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');



    const ProductItemInherit = (ProductItem)=>
    class extends ProductItem {
         constructor() {
                super(...arguments);
            }

            async updateQtyAvailable() {
            let config_id = this.env.pos.config_id;
            let qty_available = await this.rpc({
                model: 'product.product',
                method: 'get_qty_in_location',
                args: [this.props.product.id, config_id],
            });
            this.props.product.qty_available = qty_available;
        }

        get price() {
            const unitPrice = this.props.product.get_display_price(this.pricelist, 1);
            const formattedUnitPrice = this.env.pos.format_currency(unitPrice.toFixed(2), 'Product Price');
            this.updateQtyAvailable();
            if (this.props.product.to_weight) {
                return `${formattedUnitPrice}/${
                    this.env.pos.units_by_id[this.props.product.uom_id[0]].name
                }`;
            } else {
                return formattedUnitPrice;
            }
        }
    }





    Registries.Component.extend(ProductItem, ProductItemInherit);

    return ProductItemInherit;
});
