odoo.define('pos_coupon.Coupon', function (require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const models = require('point_of_sale.models');
    const rpc = require('web.rpc');

    models.Order = models.Order.extend({
        add_coupon_product_line: async function () {
            const original_product_id = 3562; // TODO: Hardcode - Settings
            const new_product_template_id = 4; // New product template ID
            const new_product = this.pos.db.get_product_by_id(new_product_template_id);
            if (!new_product) {
                console.error('New product not found');
                return;
            }

            const partner_id = this.get_client().id;

            const total_valid_papers = await rpc.query({
                model: 'az.coupon.paper',
                method: 'search_count',
                args: [[['coupon_book_id.partner_id', '=', partner_id], ['state', '=', 'valid']]],
            });

            let required_qty = 0;
            const order_lines = this.get_orderlines();
            order_lines.forEach(line => {
                if (line.product.id === original_product_id) {
                    required_qty += line.quantity;
                }
            });

            if (required_qty > total_valid_papers) {
                this.pos.gui.show_popup('error', {
                    'title': _t('Not enough valid coupons'),
                    'body': _t(`Requested quantity (${required_qty}) exceeds the total number of valid coupon papers (${total_valid_papers}).`),
                });
                return;
            }

            const order = this.export_as_JSON(); // This prepares the order in a format suitable for backend processing

            // Call the handle_papers function from Python and get the result
            const used_coupons = await rpc.query({
                model: 'pos.order',
                method: 'handle_papers',
                args: [order],
            });

            // Assuming used_coupons is a string or similar that can be directly used
            const full_name = "استبدال [قارورة مياه/5 جالون]" + "-" + " كوبونات: " + "," + used_coupons; // Format the result to a string, adjust according to actual data structure
            const full_name_wrapped = full_name.split(',').join('\n');

            order_lines.forEach(line => {
                if (line.product.id === original_product_id) {
                    this.add_product(new_product, {
                        price: 0,
                        product_description: full_name,
                        quantity: line.quantity,
                        extras: {
                            full_product_name: full_name_wrapped // Use the result from the RPC call here
                        }
                    });
                }
            });
        },

create_coupons: async function () {
    const order_lines = this.get_orderlines();
    for (let line of order_lines) {
        const product_name = line.get_full_product_name().toLowerCase();
        if (product_name.includes("دفتر كوبون") || product_name.includes("coupon book")) {
            const quantity = line.get_quantity();
            try {
                const coupon_id = await rpc.query({
                    model: 'pos.order',
                    method: 'create_coupon',
                    args: [line.order.uid, line.get_product().id, quantity],
                });

                // Update the product name with the returned coupon_id
                let updatedName = `${line.get_full_product_name()}  ${coupon_id}`;

                // Apply the wrapping
                const full_name_wrapped = updatedName.split(',').join('\n');

                line.set_full_product_name(full_name_wrapped);
            } catch (error) {
                console.error('Error creating coupon:', error);
                // You might want to show an error popup to the user here
                this.pos.gui.show_popup('error', {
                    'title': 'Error Creating Coupon',
                    'body': 'There was an error creating the coupon. Please try again.',
                });
            }
        }
    }
},
    });

    const POSValidateOverride = PaymentScreen =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                if (this.currentOrder.get_orderlines().length > 0) {
                    await this.currentOrder.create_coupons();
                }
                await super.validateOrder(isForceValidate);
            }
        };

    Registries.Component.extend(PaymentScreen, POSValidateOverride);

    return PaymentScreen;
});
