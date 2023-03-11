odoo.define('azbah_pos.validate', function (require) {
    "use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { isConnectionError } = require('point_of_sale.utils');

    const POSValidateOverride = PaymentScreen =>
        class extends PaymentScreen {
            /**
             * @override
             */
            async validateOrder(isForceValidate) {
                // Set the current order to (to_invoice) if it has lines
                // Ehab
                // Check Connection

                // if (!window.navigator.onLine || isConnectionError()) {
                //     throw new Error("Mafish Internet Connection!' +\n" +
                //         "\\n لا يوجد اتصال بالإنترنت';");
                //
                // }
                // else {
                    if (this.currentOrder.get_orderlines().length > 0) {
                        this.currentOrder.set_to_invoice(true);
                        this.render();
                    }
                    await super.validateOrder(isForceValidate);



                // }


            }
        };

    Registries.Component.extend(PaymentScreen, POSValidateOverride);

    return PaymentScreen;
});
