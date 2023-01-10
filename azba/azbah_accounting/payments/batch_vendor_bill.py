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

    # def create(self, vals):
    #     print(vals)
    #     bills = {}
    #     batch = super(BatchVendorbill, self).create(vals)
    #     lines = vals.get('line_ids')
    #     if lines:
    #         for line in lines:
    #             line = line[2]
    #             vendor_id = line.get('vendor_id')
    #             if vendor_id in bills.keys():
    #                 bills[vendor_id].append(line)
    #             else:
    #                 bills[vendor_id] = [line]
    #     print(bills)
    #     for bill in bills.items():
    #         new_bill = {
    #             'partner_id': bill[0], 'move_type': 'in_invoice', 'journal_id': 2
    #             , 'date': vals['date']
    #             , 'invoice_date': vals['date']
    #             # We need to add one line per product for each bill
    #             , 'invoice_line_ids': [[0, 0, {
    #                 'account_id': line['account_id']
    #                 , 'amount_currency': line['price_subtotal']
    #                 , 'debit': line['price_subtotal']
    #                 , 'name': line['note']
    #                 , 'partner_id': bill[0]
    #                 , 'price_unit': line['price']
    #                 , 'product_id': line['product_id']
    #                 , 'quantity': line['quantity']
    #             }] for line in bill[1]]
    #
    #         }
    #         # Then, we need to add two other lines to balance the Journal Entry
    #         # One line for Payables - and the other for Tax
    #         new_bill['line_ids'] = []
    #
    #         new_bill['line_ids'].append(
    #             (0, 0, {
    #                 'account_id': 42
    #                 , 'amount_currency': line['price_subtotal'] * 0.15
    #                 , 'debit': 30 #line['price_subtotal'] * 0.15
    #                 , 'name': "Purchase Tax 15%"
    #                 , 'partner_id': bill[0]
    #                 , 'price_unit':30 # line['price_subtotal'] * 0.15
    #                 , 'credit': 0
    #                 , 'quantity': 1
    #             }))
    #
    #         new_bill['line_ids'].append(
    #             (0, 0, {
    #                 'account_id': 54
    #                 , 'date_maturity': self.date
    #                 , 'amount_currency': line['price_subtotal'] * -1.15
    #                 , 'credit': 230 # line['price_subtotal'] * 1.15
    #                 , 'price_unit': -230
    #                 # , 'name': "Purchase Tax 15%"
    #                 , 'partner_id': bill[0]
    #                 , 'debit': 0
    #                 , 'quantity': 1
    #             }))
    #         new_bill['line_ids'].append(new_bill['invoice_line_ids'][:][0])
    #
    #         invoice = self.env['account.move'].sudo().create(new_bill)
    #         invoice.action_post()
    #
    #     return batch

    @api.model
    def create(self, vals_list):
        # Define a list of vendors and amounts

        # Loop through the list and create a vendor bill for each vendor

        # url = "http://localhost"
        # db = "azbah"
        # username = "admin"
        # password = "zzzz"
        #
        # common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        # uid = common.authenticate(db, username, password, {})
        # _models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
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
            # _id = _models.execute_kw(db, uid, password, 'account.move', 'create', [new_bill])

            _bill = self.env['account.move'].create(new_bill)
            # _bill = self.env['account.move'].search([('id', '=', _id)])
            _bill.action_post()

            # cntx = {'origin': 'batch', 'active_model': 'account.move', 'active_id': _bill.id, 'active_ids': [_bill.id]}
            # p = self.env['account.payment.register'].sudo().with_context(cntx).action_create_payments()
            # c = p

        # new_bill = self.create_vendor_bill()
        # _id = _models.execute_kw(db, uid, password, 'account.move', 'create', [[[new_bill]]])
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
#
#
# class AccountPaymentRegister(models.TransientModel):
#     _inherit = 'account.payment.register'
#
#     def _create_payments(self):
#         if not self._context.get('origin') == 'batch':
#             self.ensure_one()
#         batches = self._get_batches()
#         edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
#         to_process = []
#
#         if edit_mode:
#             payment_vals = self._create_payment_vals_from_wizard()
#             to_process.append({
#                 'create_vals': payment_vals,
#                 'to_reconcile': batches[0]['lines'],
#                 'batch': batches[0],
#             })
#         else:
#             # Don't group payments: Create one batch per move.
#             if not self.group_payment:
#                 new_batches = []
#                 for batch_result in batches:
#                     for line in batch_result['lines']:
#                         new_batches.append({
#                             **batch_result,
#                             'lines': line,
#                         })
#                 batches = new_batches
#
#             for batch_result in batches:
#                 to_process.append({
#                     'create_vals': self._create_payment_vals_from_batch(batch_result),
#                     'to_reconcile': batch_result['lines'],
#                     'batch': batch_result,
#                 })
#
#         payments = self._init_payments(to_process, edit_mode=edit_mode)
#         self._post_payments(to_process, edit_mode=edit_mode)
#         self._reconcile_payments(to_process, edit_mode=edit_mode)
#         return payments
#
#     def _get_batches(self):
#         ''' Group the account.move.line linked to the wizard together.
#         Lines are grouped if they share 'partner_id','account_id','currency_id' & 'partner_type' and if
#         0 or 1 partner_bank_id can be determined for the group.
#         :return: A list of batches, each one containing:
#             * payment_values:   A dictionary of payment values.
#             * moves:        An account.move recordset.
#         '''
#         if not self._context.get('origin') == 'batch':
#             self.ensure_one()
#
#         lines = self.line_ids._origin
#         if not self._context.get('origin') == 'batch':
#             if len(lines.company_id) > 1:
#                 raise UserError(_("You can't create payments for entries belonging to different companies."))
#             if not lines:
#                 raise UserError(_("You can't open the register payment wizard without at least one receivable/payable line."))
#
#         batches = defaultdict(lambda: {'lines': self.env['account.move.line']})
#         for line in lines:
#             batch_key = self._get_line_batch_key(line)
#             serialized_key = '-'.join(str(v) for v in batch_key.values())
#             vals = batches[serialized_key]
#             vals['payment_values'] = batch_key
#             vals['lines'] += line
#
#         # Compute 'payment_type'.
#         for vals in batches.values():
#             lines = vals['lines']
#             balance = sum(lines.mapped('balance'))
#             vals['payment_values']['payment_type'] = 'inbound' if balance > 0.0 else 'outbound'
#
#         return list(batches.values())