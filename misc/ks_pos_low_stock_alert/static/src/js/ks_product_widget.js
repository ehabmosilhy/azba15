odoo.define('ks_pos_low_stock_alert.ksProductWidget', function(require) {
    'use strict';

    const { useState } = owl;
    const { patch } = require('web.utils');
    const PosComponent = require('point_of_sale.ProductsWidget');
    const Registries = require('point_of_sale.Registries');

    patch(PosComponent.prototype, 'ks_pos_low_stock_alert.KsProductWidget', {
        get productsToDisplay() {
            const list = this._super();
            return list.sort((a, b) => b.qty_available - a.qty_available);
        }

    })

});
