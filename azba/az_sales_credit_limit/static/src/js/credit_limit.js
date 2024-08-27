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

                // Check if any of the payment lines are credit payments
                const paymentLines = order.get_paymentlines();
                const isCreditPayment = paymentLines.some(line => line.payment_method && (line.payment_method.type === 'credit' || line.payment_method.type === 'pay_later'));

                // 🕵️‍♂️ Check if partner is set, has a credit limit category, and is paying with credit.
                if (partner && partner.credit_limit_category_id && isCreditPayment) {

                    // Get the current session's orders
                    const sessionOrders = this.env.pos.get_order_list();

                    // Filter orders to only include those made by the specific customer
                    const customerOrders = sessionOrders.filter(order => order.get_client() && order.get_client().id === partner.id);

                    // Calculate the total amount paid or deposited by the customer during the session
                    const totalSessionPayments = customerOrders.reduce((total, order) => {
                        return total + order.get_total_with_tax(); // Sum the total amount of each order
                    }, 0);

                    // Retrieve the customer's credit limit
                    const creditLimitCategory = this.env.pos.credit_limit_category_by_id[partner.credit_limit_category_id[0]];
                    const creditLimit = creditLimitCategory ? creditLimitCategory.credit_limit : 0;

                    // Adjust the total due considering the payments or deposits made during the session
                    const adjustedTotalDue = partner.total_due - totalSessionPayments;
                    const totalAmount = order.get_total_with_tax() + adjustedTotalDue;

                    // 🚨 If order amount exceeds credit limit, show error popup and return false.
                    if (totalAmount > creditLimit) {
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
