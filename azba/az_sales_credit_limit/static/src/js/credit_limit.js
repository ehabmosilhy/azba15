//  🚀📈
// Extend the functionality to include a credit limit check during the payment process. If a customer exceeds their
// credit limit, an error is displayed and the order cannot be validated.
//  📉🚀

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

                // 🕵️‍♂️ Check if partner is set and has a credit limit category.
                if (partner && partner.credit_limit_category_id) {
                    const creditLimitCategory = this.env.pos.credit_limit_category_by_id[partner.credit_limit_category_id[0]];
                    const creditLimit = creditLimitCategory ? creditLimitCategory.credit_limit : 0;
                    const totalAmount = order.get_total_with_tax() + partner.total_due; // 🔄 Updated to include 'total_due' in the check

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