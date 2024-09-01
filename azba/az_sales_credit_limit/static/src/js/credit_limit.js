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
                let isOneOrder = false;// False;
                let isPayment = false; // False;
                let dontCheck = false; // False;
                // if the order is paid with cash, don't check the credit limit
                // the due_amount is negative if settlement and zero if the order buying with cash
                // This order doesn't need checking and doesn't affect the total due amount
                const paid_with_cash = order.is_paid_with_cash()
                if (paid_with_cash)
                    dontCheck = true;

                if (partner && partner.credit_limit_category_id && !dontCheck) {

                    // Get the current session's orders
                    const sessionOrders = this.env.pos.get_order_list();

                    // Filter orders to only include those made by the specific customer
                    const customerOrders = sessionOrders.filter(o => o.get_client() && o.get_client().id === partner.id);

                    // Calculate the total due amount by analyzing payment lines, excluding the current order
                    let adjustedTotalDue = partner.total_due;

                    customerOrders.forEach(o => {

                        let is_paid_with_cash = o.is_paid_with_cash();
                        let is_settlement = o.is_settlement();

                        // buy and pay with cash (doesn't affect the total due amount)
                        //    if (is_paid_with_cash && due >=0) {
                        //     adjustedTotalDue +=0;
                        //    }
                        // settlement with cash
                        if (is_paid_with_cash && is_settlement) {
                            // adjustedTotalDue -= o.get_total_paid(); 
                            // get payment lines
                            let pl = o.get_paymentlines()[0];
                            let amount = pl.amount;
                            adjustedTotalDue -= Math.abs(amount);
                        }
                        // buy and pay with credit
                        if (!is_paid_with_cash && !is_settlement) {
                            adjustedTotalDue += o.get_total_paid();
                        }

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
