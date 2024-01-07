odoo.define('az_pos_traceability_validation.pos_models', function (require) {
    "use strict";
    const EditListPopup = require('point_of_sale.EditListPopup');
    const Registries = require('point_of_sale.Registries');
    let core = require('web.core');
    // Ehab
    let _t = core._t;
    var rpc = require('web.rpc');

    const PosEditlistpopup = (EditListPopup) =>
        class extends EditListPopup {

         constructor() {
                super(...arguments);
                if (this.props.title === this.env._t("Lot/Serial Number(s) Required")) {
                    this.props.product=this.env.session.product;
                    this.props.config_id=this.env.session.config_id;
                }
            }
            async confirm() {
                // Ehab: Enable Translation
                if (this.props.title == _t('Lot/Serial Number(s) Required')) {

                    var lot_string = this.state.array
                    var lot_names = [];
                    for (var i = 0; i < lot_string.length; i++) {

                        if (lot_string[i].text != "") {
                            lot_names.push(lot_string[i].text);
                        }

                    }
                    // Ehab: get current config id
                    let config_id=this.props.config_id;
                    let product_id=this.props.product.id;

                    // try {
                    //     // Assuming self.location.href is 'http://localhost/pos/ui?config_id=28#cids=1'
                    //     let location = self.location.href;
                    //
                    //     // Create a URL object
                    //     let url = new URL(location);
                    //
                    //     // Use URLSearchParams to parse the query parameters
                    //     let searchParams = new URLSearchParams(url.search);
                    //
                    //     // Get the config_id parameter from the URL
                    //     config_id = searchParams.get('config_id');
                    // } catch (error) {
                    //     console.error("Error extracting config_id:", error);
                    //     config_id = null;
                    // }

                    // Now you can use config_id in your rpc call
                    // If there was an error, config_id will be null
                    const result = await rpc.query({
                        model: 'serial_no.validation',
                        method: 'validate_lots',
                        args: [lot_names, config_id, product_id]
                    });


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