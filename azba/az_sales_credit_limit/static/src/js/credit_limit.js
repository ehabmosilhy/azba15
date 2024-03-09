// Include the required modules using the 'require' function provided by Odoo's JavaScript framework.
odoo.define('az_sales_credit_limit.credit_limit', function (require) {
    "use strict";

    // The 'models' module provides access to the data models used in the POS.
    const models = require('point_of_sale.models');

    // The 'PaymentScreen' component is the base class for the payment screen in the POS.
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    // The 'Registries' module is used to register components for extension or addition.
    const Registries = require('point_of_sale.Registries');

    // Load additional fields into the 'res.partner' and 'credit.limit.category' models.
    // This is necessary to access the credit limit data in the POS.
    models.load_fields('res.partner', ['credit_limit_category_id']);
    models.load_fields('credit.limit.category', ['credit_limit']);

    // Store the original 'initialize' method of 'PosModel' to call it later inside the extended version.
    const PosModelSuper = models.PosModel.prototype;

    // Extend 'PosModel' to include the credit limit category data when initializing.
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            // Call the original initialize method of 'PosModel'.
            PosModelSuper.initialize.apply(this, arguments);

            // Add a new model to the list of models to load at initialization.
            // This action ensures that the credit limit categories are loaded into the POS.
            this.models.push({
                model: 'credit.limit.category',
                fields: ['credit_limit'],
                loaded: (self, credit_limit_categories) => {
                    // Create a dictionary to store the credit limit categories by their ID for easy access.
                    self.credit_limit_category_by_id = {};
                    credit_limit_categories.forEach(category => {
                        self.credit_limit_category_by_id[category.id] = category;
                    });
                },
            });
        },
    });

    // Define a new class by extending the 'PaymentScreen' component.
    // This extension will add custom logic to the payment validation process.
    const CreditLimitPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            // The 'validateOrder' method is overridden to include the credit limit check.
            async validateOrder(isForceValidate) {
                const order = this.env.pos.get_order();
                const partner = order.get_client();

                // Perform a check only if the customer is set and has a credit limit category.
                if (partner && partner.credit_limit_category_id) {
                    // Retrieve the credit limit category based on the customer's category ID.
                    const creditLimitCategory = this.env.pos.credit_limit_category_by_id[partner.credit_limit_category_id[0]];
                    // Get the credit limit from the category, defaulting to 0 if not found.
                    const creditLimit = creditLimitCategory ? creditLimitCategory.credit_limit : 0;
                    // Calculate the total amount of the order.
                    const totalAmount = order.get_total_with_tax();

                    // If the order amount exceeds the customer's credit limit, display an error popup.
                    if (totalAmount > creditLimit) {
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Credit Limit Exceeded'),
                            body: this.env._t('The credit limit has been exceeded for the customer ') + partner.name,
                        });
                        return false;
                    }
                }
                // If the credit limit is not exceeded or not applicable, proceed with the normal validation process.
                return super.validateOrder(isForceValidate);
            }
        };

    // Register the extension of the 'PaymentScreen' component.
    // This step is necessary to apply the custom behavior defined in the extension.
    Registries.Component.extend(PaymentScreen, CreditLimitPaymentScreen);

    // Return the extended 'PaymentScreen' component class,
    // making it available for use in the POS application.
    return CreditLimitPaymentScreen;
});