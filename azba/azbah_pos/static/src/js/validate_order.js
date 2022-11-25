odoo.define('azbah_pos.validate', function (require) {
    "use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const POSValidateOverride = PaymentScreen =>
        class extends PaymentScreen {
            /**
             * @override
             */
            async validateOrder(isForceValidate) {
                // Set the current order to (to_invoice) if it has lines
                // Ehab
                // Check Connection
                let connection_status = this.env.pos.get('synch').status;
                if (connection_status==='connected') {
                    if (this.currentOrder.get_orderlines().length > 0) {
                        this.currentOrder.set_to_invoice(true);
                        this.render();
                    }
                    await super.validateOrder(isForceValidate);
                }
                else {
                     throw 'No Internet! \n لا يوجد اتصال بالإنترنت';
                }

            }
        };

    Registries.Component.extend(PaymentScreen, POSValidateOverride);

    return PaymentScreen;
});
