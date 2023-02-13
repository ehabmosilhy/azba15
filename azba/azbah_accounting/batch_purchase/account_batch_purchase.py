# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BatchPurchase(models.Model):
    _name = "account.batch.purchase"
    delegate_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date(required=True)
    total = fields.Float()
    line_ids = fields.One2many('account.batch.purchase.line', 'batch_id')

    @api.onchange('line_ids')
    def onchange_price_or_qty(self):
        total = 0
        for line in self.line_ids:
            total += line.price_subtotal
        self.total = total

    @api.model
    def create(self, vals_list):
        orders = {}
        batch_lines = vals_list.get('line_ids')
        if batch_lines:
            for batch_line in batch_lines:
                line = batch_line[2]
                vendor_id = line.get('vendor_id')
                if vendor_id in orders.keys():
                    orders[vendor_id].append(line)
                else:
                    orders[vendor_id] = [line]
        print(orders)
        for order in orders.items():
            vendor_id = order[0]
            bill_lines = order[1]

            new_order = {
                "priority": "0",
                'partner_id': vendor_id,
                "currency_id": 148,
                "picking_type_id": 551
                , 'date_order': vals_list['date']
                , 'date_planned': vals_list['date']
                , 'order_line': [
                    (0, 0,
                     {
                         "sequence": 10,
                         'product_id': _line['product_id'],
                         "date_planned": vals_list['date'],
                         "product_uom": 1
                         , 'name': _line['note']
                         , 'price_unit': _line['price']
                         , 'product_qty': _line['quantity']
                     }) for _line in bill_lines]
            }

            _order = self.env['purchase.order'].create(new_order)
            _order.button_confirm()
            for picking in _order.picking_ids:
                picking.button_validate()
        batch = super(BatchPurchase, self).create(vals_list)
        return batch


class BatchVendorBillLine(models.Model):
    _name = "account.batch.purchase.line"
    batch_id = fields.Many2one('account.batch.purchase')
    vendor_id = fields.Many2one('res.partner', tracking=True,
                                string='Vendor', change_default=True, domain=[('code', 'ilike', 'v%')])
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    quantity = fields.Float()
    price = fields.Float()
    price_subtotal = fields.Float()
    note = fields.Html()
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        help="Taxes that apply on the base amount"
        , default=[5]  # Purchase Tax 15%
    )

    @api.onchange('price', 'quantity')
    def onchange_price_or_qty(self):
        self.price_subtotal = float(self.price) * float(self.quantity)
