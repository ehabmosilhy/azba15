# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BatchPurchase(models.Model):
    _name = "account.batch.purchase"
    delegate_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date(required=True)
    total = fields.Float()
    vendor_count = fields.Selection([
        ('single', 'Single'),
        ('multi', 'Multi'),
    ], string='Vendors', default='single'
    )
    vendor_id = fields.Many2one('res.partner', tracking=True,
                                string='Vendor', change_default=True, domain=[('code', 'ilike', 'v%')])

    line_ids = fields.One2many('account.batch.purchase.line', 'batch_id')

    # Update the Total
    @api.onchange('line_ids')
    def onchange_price_or_qty(self):
        total = 0
        for line in self.line_ids:
            total += line.price_subtotal_with_tax
        self.total = total

    @api.model
    def create(self, vals_list):
        orders = {}
        batch_lines = vals_list.get('line_ids')

        # We need to group the lines by vendor to make all the lines of one vendor together in
        # one purchase order
        if batch_lines:
            for batch_line in batch_lines:
                line = batch_line[2]
                # if the user doesn't enter a note, make it empty without the HTML characters
                if '<br' in line['note']:
                    line['note'] = ""
                vendor_id = line.get('vendor_id')
                if vendor_id in orders.keys():
                    orders[vendor_id].append(line)
                else:
                    orders[vendor_id] = [line]

        for order in orders.items():
            if vals_list.get('vendor_count') == 'single':
                vendor_id = vals_list.get('vendor_id')
            else:
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
                         "sequence": 10
                         , 'product_id': _line['product_id']
                         , 'name': _line['note']
                         , "date_planned": vals_list['date']
                         , "product_uom": _line['product_uom']
                         , 'price_unit': _line['price']
                         , 'product_qty': _line['quantity']
                     }) for _line in bill_lines]
            }
            # Create the purchase order
            _order = self.env['purchase.order'].create(new_order)

            # Confirm the order
            _order.button_confirm()

            # Validate the picking
            for picking in _order.picking_ids:
                for line in picking.move_ids_without_package:
                    # receive all the quantity
                    line.quantity_done = line.product_uom_qty
                picking.button_validate()

            # Create the Vendor Bill
            _order.action_create_invoice()

        batch = super(BatchPurchase, self).create(vals_list)
        return batch


class BatchVendorBillLine(models.Model):
    _name = "account.batch.purchase.line"
    batch_id = fields.Many2one('account.batch.purchase')
    vendor_id = fields.Many2one('res.partner', tracking=True,
                                string='Vendor', change_default=True, domain=[('code', 'ilike', 'v%')])
    vendor_count = fields.Selection(related="batch_id.vendor_count")
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    quantity = fields.Float()
    price = fields.Float()
    price_subtotal = fields.Float(string="Sub Total")
    price_subtotal_with_tax = fields.Float(string="With Tax")
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
        self.price_subtotal_with_tax = float(self.price_subtotal) * 1.15
