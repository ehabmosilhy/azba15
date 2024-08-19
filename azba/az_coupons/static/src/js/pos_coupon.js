odoo.define('pos_coupon.Coupon', function (require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const models = require('point_of_sale.models');
    const rpc = require('web.rpc');
    const {Gui} = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const {useListener} = require('web.custom_hooks');

    models.Order = models.Order.extend({
        add_coupon_product_line: async function () {
            const original_product_id = 3562;  // فوارغ كوبون
            const new_product_template_id = 4; // قارورة مياه/5 جالون
            const new_product = this.pos.db.get_product_by_id(new_product_template_id);
            if (!new_product) {
                console.error('New product not found');
                return false;
            }
            const partner_id = this.get_client().id;
            const total_valid_pages = await rpc.query({
                model: 'az.coupon.page',
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
            if (required_qty > total_valid_pages) {
                Gui.showPopup('ErrorPopup', {
                    title: 'Not enough valid coupons',
                    body: `Requested quantity (${required_qty}) exceeds the total number of valid coupon pages (${total_valid_pages}).`,
                });
                return false;
            }

            const order = this.export_as_JSON();
            const used_coupons = await rpc.query({
                model: 'pos.order',
                method: 'handle_pages',
                args: [order],
            });
            const full_name = "استبدال [قارورة مياه/5 جالون]" + "-" + " كوبونات: " + "," + used_coupons;
            const full_name_wrapped = full_name.split(',').join('\n');
            order_lines.forEach(line => {
                if (line.product.id === original_product_id) {
                    this.add_product(new_product, {
                        price: 0,
                        product_description: full_name,
                        quantity: line.quantity,
                        extras: {full_product_name: full_name_wrapped}
                    });
                }
            });
            return true;
        },
        create_coupons: async function () {
            const order_lines = this.get_orderlines();
            for (let line of order_lines) {
                const product_name = line.get_full_product_name().toLowerCase();
                if (product_name.includes("دفتر كوبون") || product_name.includes("coupon book")) {
                    const quantity = line.get_quantity();
                    const partner_id = this.get_client().id;
                    try {
                        const coupon_id = await rpc.query({
                            model: 'pos.order',
                            method: 'create_coupon',
                            args: [line.order.uid,partner_id, line.get_product().id, quantity],
                        });
                        let updatedName = `${line.get_full_product_name()}  ${coupon_id}`;
                        const full_name_wrapped = updatedName.split(',').join('\n');
                        line.set_full_product_name(full_name_wrapped);
                    } catch (error) {
                        console.error('Error creating coupon:', error);
                        Gui.showPopup('ErrorPopup', {
                            title: 'Error Creating Coupon',
                            body: 'There was an error creating the coupon. Please try again.',
                        });
                    }
                }
            }
        },
    });

    const POSValidateOverride = PaymentScreen => class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            if (this.currentOrder.get_orderlines().length > 0) {

                const order_lines = this.currentOrder.get_orderlines();

                const containsCouponBook = order_lines.some(line => [37, 38,3562].includes(line.product.id));
                // 3562 is Coupon Page
                if (order_lines.length > 1 && containsCouponBook) {
                    Gui.showPopup('ErrorPopup', {
                        title: "Invalid Order",
                        body: "You can't sell the Coupons with any other product, each coupon book must be sold alone!",
                    });
                    return false;
                }


                await this.currentOrder.create_coupons();
                const canProceed = await this.currentOrder.add_coupon_product_line();
                if (!canProceed) {
                    return;
                }
            }
            await super.validateOrder(isForceValidate);
        }
    };

    Registries.Component.extend(PaymentScreen, POSValidateOverride);
    return PaymentScreen;
});

// Popup definition
odoo.define('pos_coupon.CouponProductsPopup', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const {useState} = owl.hooks;
    const {useListener} = require('web.custom_hooks');

    class CouponProductsPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener('click-product', this._clickProduct);
        }

        get productsToDisplay() {
            return this.env.pos.db.get_product_by_category(this.env.pos.config.category_id[0]);
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        async _clickProduct(event) {
            if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }

            const product = event.detail;
            const order = this.currentOrder;
            order.add_product(product);
        }
    }

    CouponProductsPopup.template = 'CouponProductsPopup';
    CouponProductsPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Coupon Products',
        body: '',
    };

    Registries.Component.add(CouponProductsPopup);
    return CouponProductsPopup;
});
