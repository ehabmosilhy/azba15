odoo.define('pos_traceability_validation.pos_models', function (require) {
    "use strict";
    const EditListPopup = require('point_of_sale.EditListPopup');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');

    const PosEditlistpopup = (EditListPopup) =>
        class extends EditListPopup {
            async confirm() {

                if (this.props.title == 'Lot/Serial Number(s) Required') {

                    var lot_string = this.state.array
                    var lot_names = [];
                    for (var i = 0; i < lot_string.length; i++) {

                        if (lot_string[i].text != "") {
                            lot_names.push(lot_string[i].text);
                        }

                    }

                    const result = await rpc.query({
                        model: 'serial_no.validation',
                        method: 'validate_lots',
                        args: [lot_names]
                    })

                    if (result != true) {
                        if (result[0] == 'no_stock') {
                            this.showPopup('ErrorPopup', {
                                'title': this.env._t('Insufficient stock'),
                                'body': this.env._t("Insufficient stock for " + result[1]),
                            });

                        } else if (result[0] == 'duplicate') {
                            this.showPopup('ErrorPopup', {
                                'title': this.env._t('Duplicate entry'),
                                'body': this.env._t("Duplicate entry for " + result[1]),
                            });
                        } else if (result[0] == 'except') {
                            alert("Exception occured with " + result[1])
                            this.showPopup('ErrorPopup', {
                                'title': this.env._t('Exception'),
                                'body': this.env._t("Exception occured with" + result[1]),
                            });
                        }
                    } else {
                        this.props.resolve({confirmed: true, payload: await this.getPayload()});
                        this.trigger('close-popup');

                    }
                } else {
                    this.props.resolve({confirmed: true, payload: await this.getPayload()});
                    this.trigger('close-popup');
                }

            }

        };

    Registries.Component.extend(EditListPopup, PosEditlistpopup);

    return EditListPopup;


});


odoo.define('pos_traceability_validation.qty', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _super_orderline = models.Orderline.prototype;

    models.Orderline = models.Orderline.extend({
        set_quantity: function (quantity, keep_price) {
            if (quantity !== '') {
                // Your code here. This will be executed before the quantity is changed.

                // Ehab
                console.log('Changing quantity to: ' + quantity);
            }

            // Call the original method
            _super_orderline.set_quantity.call(this, quantity, keep_price);
            console.log('=== Qty Changed Successfully');
            this.update_serials(this.pack_lot_lines, quantity);  // Use 'this' to call the method

        },
        update_serials: function (packlot, qty) {
            if (qty !== '' && packlot.length > 0) {
                let first_lot = parseInt(packlot.models[0].attributes.lot_name);
                packlot.models = [packlot.models[0]]; // Keep only the first model

                for (let i = 1; i < qty; i++) {
                    // let newModel = JSON.parse(JSON.stringify(packlot.models[0])); // Deep copy of the first model
                    let newModel = Object.assign({}, packlot.models[0]);
                    newModel.attributes.lot_name = (first_lot + i).toString();
                    packlot.models.push(newModel); // Add the new model to the array
                }
            }
        }

        // update_serials: function (packlot, qty) {
        //     if (qty !== 'remove') {
        //         let first_lot = packlot.length ? parseInt(packlot.models[0].attributes.lot_name) : 0;
        //         for (let i = 0; i < packlot.length; i++) {
        //             packlot.models[i].attributes.lot_name = (first_lot + i).toString();
        //         }
        //     }
        // }

    });
});