# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BatchVendorbill(models.Model):
    _name = "account.batch.vendor.bill"

    delegate_id = fields.Many2one('hr.employee')
    date = fields.Datetime()
    total = fields.Float()
    move_ids = fields.One2many('account.move', 'batch_id')
    line_ids = fields.One2many('account.batch.vendor.bill.line', 'batch_id')

    @api.model
    def create(self, vals):
        print(vals)
        bills = {}
        batch = super(BatchVendorbill, self).create(vals)
        lines = vals.get('line_ids')
        if lines:
            for line in lines:
                line = line[2]
                vendor_id = line.get('vendor_id')
                if vendor_id in bills.keys():
                    bills[vendor_id].append(line)
                else:
                    bills[vendor_id] = [line]
        print(bills)
        for bill in bills.items():
            new_bill = {
                'partner_id': bill[0], 'move_type': 'in_invoice', 'journal_id': 2
                , 'date': vals['date']
                , 'invoice_date': vals['date']
                # We need to add one line per product for each bill
                , 'invoice_line_ids': [(0, 0, {
                    'account_id': line['account_id']
                    , 'amount_currency': line['price_subtotal']
                    , 'debit': line['price_subtotal']
                    , 'name': line['note']
                    , 'partner_id': bill[0]
                    , 'price_unit': line['price']
                    , 'product_id': line['product_id']
                    , 'quantity': line['quantity']
                }) for line in bill[1]]

            }
            # Then, we need to add two other lines to balance the Journal Entry
            # One line for Payables - and the other for Tax
            new_bill['line_ids'] = []

            new_bill['line_ids'].append(
                (0, 0, {
                    'account_id': 42
                    , 'amount_currency': line['price_subtotal'] * 0.15
                    , 'debit': 30 #line['price_subtotal'] * 0.15
                    , 'name': "Purchase Tax 15%"
                    , 'partner_id': bill[0]
                    , 'price_unit':30 # line['price_subtotal'] * 0.15
                    , 'credit': 0
                    , 'quantity': 1
                }))

            new_bill['line_ids'].append(
                (0, 0, {
                    'account_id': 54
                    , 'date_maturity': self.date
                    , 'amount_currency': line['price_subtotal'] * -1.15
                    , 'credit': 230 # line['price_subtotal'] * 1.15
                    , 'price_unit': -230
                    # , 'name': "Purchase Tax 15%"
                    , 'partner_id': bill[0]
                    , 'debit': 0
                    , 'quantity': 1
                }))
            new_bill['line_ids'].append(new_bill['invoice_line_ids'][:])

            invoice = self.env['account.move'].sudo().create(new_bill)
            invoice.action_post()

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
                                 tracking=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    quantity = fields.Float()
    price = fields.Float()
    price_subtotal = fields.Float()
    note = fields.Html()

    @api.onchange('price', 'quantity')
    def onchange_price_or_qty(self):
        self.price_subtotal = float(self.price) * float(self.quantity)
