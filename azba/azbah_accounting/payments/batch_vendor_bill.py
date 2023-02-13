# -*- coding: utf-8 -*-
import time
import xmlrpc.client
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict


class BatchVendorbill(models.Model):
    _name = "account.batch.vendor.bill"

    delegate_id = fields.Many2one('hr.employee')
    date = fields.Datetime()
    total = fields.Float()
    move_ids = fields.One2many('account.move', 'batch_id')
    line_ids = fields.One2many('account.batch.vendor.bill.line', 'batch_id')

    @api.model
    def create(self, vals_list):
        bills = {}
        batch_lines = vals_list.get('line_ids')
        if batch_lines:
            for batch_line in batch_lines:
                line = batch_line[2]
                vendor_id = line.get('vendor_id')
                if vendor_id in bills.keys():
                    bills[vendor_id].append(line)
                else:
                    bills[vendor_id] = [line]
        print(bills)
        for bill in bills.items():
            vendor_id = bill[0]
            bill_lines = bill[1]
            new_bill = {
                'partner_id': vendor_id,
                'move_type': 'in_invoice',
                'journal_id': 2
                , 'invoice_date': vals_list['date']
                , 'invoice_line_ids': [
                    (0, 0,
                     {
                         'account_id': 76
                         , 'amount_currency': _line['price_subtotal']
                         , 'name': _line['note']
                         , 'partner_id': vendor_id
                         , 'price_unit': _line['price']
                         , 'product_id': _line['product_id']
                         , 'quantity': _line['quantity']
                         , 'tax_ids': _line['tax_ids']
                     }) for _line in bill_lines]
            }

            _bill = self.env['account.move'].create(new_bill)
            _bill.action_post()

        batch = super(BatchVendorbill, self).create(vals_list)
        return batch


class BatchVendorBillLine(models.Model):
    _name = "account.batch.vendor.bill.line"
    batch_id = fields.Many2one('account.batch.vendor.bill')
    # move_id = fields.Many2one('account.move')
    vendor_id = fields.Many2one('res.partner', tracking=True,
                                string='Vendor', change_default=True, domain=[('code', 'ilike', 'v%')])
    account_id = fields.Many2one('account.account', string='Account',
                                 index=True, ondelete="cascade",
                                 domain="[('deprecated', '=', False),('is_off_balance', '=', False)]",
                                 tracking=True
                                 , default=76  # cost of goods sold in trading
                                 )
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
