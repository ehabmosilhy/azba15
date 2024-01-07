/*
    Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
odoo.define("az_pos_traceability_validation.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const PosLotSaleProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            /**
             * @override
             */
            async _getAddProductOptions(product) {
                if (["serial", "lot"].includes(product.tracking)) {
                    //Ehab
                    this.env.session.product = product;
                    this.env.session.config_id = this.env.pos.config_id;
                }
                const res = await super._getAddProductOptions(...arguments);
                this.env.session.lots = undefined;
                return res;
            }
        };

    Registries.Component.extend(ProductScreen, PosLotSaleProductScreen);
    return ProductScreen;
});
