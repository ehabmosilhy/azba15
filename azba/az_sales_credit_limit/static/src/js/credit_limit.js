odoo.define('az_sales_credit_limit.credit_limit', function (require) {
    "use strict";

    // 🧰 Require necessary modules from the POS application.
    const models = require('point_of_sale.models');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    // 📝 Load additional fields required for the credit limit check.
    models.load_fields('res.partner', ['credit_limit_category_id', 'total_due']); // 🆕 Added 'total_due' field

    // 🛠️ Store a reference to the original PosModel initialize function.
    const PosModelSuper = models.PosModel.prototype;

    // 🔧 Extend the PosModel to include loading of credit limit categories.
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            PosModelSuper.initialize.apply(this, arguments);

            // ➕ Push a new model to the models list to load credit limit categories.
            this.models.push({
                model: 'credit.limit.category',
                fields: ['credit_limit'],
                loaded: (self, credit_limit_categories) => {
                    self.credit_limit_category_by_id = {};
                    credit_limit_categories.forEach(category => {
                        self.credit_limit_category_by_id[category.id] = category;
                    });
                },
            });
        },
    });

    // 🎨 Extend PaymentScreen to include the updated credit limit check in the order validation.
    const CreditLimitPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                const order = this.env.pos.get_order();
                const partner = order.get_client();

                // 🕵️‍♂️ Check if partner is set, has a credit limit category, and is paying with credit.
                if (partner && partner.credit_limit_category_id) {

                    // Get the current session's orders
                    const sessionOrders = this.env.pos.get_order_list();

                    // Filter orders to only include those made by the specific customer
                    const customerOrders = sessionOrders.filter(o => o.get_client() && o.get_client().id === partner.id && o !== order);

                    // Calculate the total due amount by analyzing payment lines, excluding the current order
                    let adjustedTotalDue = partner.total_due;

                    customerOrders.forEach(o => {
                        o.get_paymentlines().forEach(line => {
                            const amount = line.get_amount();
                            const isCash = line.payment_method.is_cash_count;

                            if (amount > 0 && isCash) {
                                // Positive cash payment reduces the due amount
                                adjustedTotalDue -= amount;
                            } else if (amount > 0 && !isCash) {
                                // Positive non-cash payment increases the due amount
                                adjustedTotalDue += amount;
                            }
                            // If amount is negative and is_cash_count is false, do nothing
                        });
                    });

                    // Retrieve the customer's credit limit
                    const creditLimitCategory = this.env.pos.credit_limit_category_by_id[partner.credit_limit_category_id[0]];
                    const creditLimit = creditLimitCategory ? creditLimitCategory.credit_limit : 0;

                    // 🚨 If the adjusted total due amount exceeds the credit limit, show error popup and return false.
                    if (adjustedTotalDue > creditLimit) {
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Credit Limit Exceeded'),
                            body: this.env._t('The total amount exceeds the customer\'s credit limit for: ') + partner.name,
                        });
                        return false;
                    }
                }
                // ✅ If no issues, proceed with normal validation.
                return super.validateOrder(isForceValidate);
            }
        };

    // 📌 Register the extended PaymentScreen component.
    Registries.Component.extend(PaymentScreen, CreditLimitPaymentScreen);

    // 📦 Return the extended component for use in the POS.
    return CreditLimitPaymentScreen;
});
