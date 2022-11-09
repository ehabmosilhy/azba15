// odoo.define('azbah_pos.getInvoiceNumber', function (require) {
//     "User strict";
//     var rpc = require('web.rpc');
//     let order = this.pos.get_order();
//     let domain = [('ref', '=', order.name)]
//     let fields = "name"
//     var getInvoice = rpc.query({
//         model: 'account.move',
//         method: 'read',
//         args: [domain, fields],
//         context: context
//     })
//     return getInvoice;
//
// })
//
