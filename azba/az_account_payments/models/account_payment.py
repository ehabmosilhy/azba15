# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"
    amount = fields.Monetary(required=True)
    is_sanad = fields.Boolean()
    taxes_id = fields.Many2many('account.tax', string='الضرائب', default=lambda self: self._default_tax_ids())
    sanad_type = fields.Selection([
        ('out', 'Outbound'),
        ('in', 'Inbound'),
        ('bank', 'Bank')
    ])

    @api.model
    def _default_tax_ids(self):
        if self._context.get('default_is_internal_transfer'):
            purchase_tax = self.env['account.tax'].search([('id', '=', '5')])  # Hardcoded: Purchase Tax
            return purchase_tax
        return self.env['account.tax']

    @api.constrains('amount', 'partner_id')
    def _check_amount_and_partner(self):
        ctx=self._context
        if ctx.get('active_model')!='account.payment':
            return
        for pay in self:
            if pay.amount <= 0:
                raise ValidationError(_('القيمة يجب أن تكون أكبر من صفر.'))

    def _prepare_payment_display_name(self):

        #  /\_/\
        # ( ◕‿◕ )
        #  >   <
        # Beginning: Ehab

        if self.env.context.get('sanad'):
            return {
                'outbound-customer': _(""),
                'inbound-customer': _(""),
                'outbound-supplier': _(""),
                'inbound-supplier': _(""),
            }
        else:
            return {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }

    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):

        for pay in self:

            #  /\_/\
            # ( ◕‿◕ )
            #  >   <
            # Beginning: Ehab
            # The payment method gets recalculated after the creation of the payment
            if self.env.context.get('sanad'):
                pay.payment_method_line_id = 2 if self.env.context.get('default_payment_type') == 'outbound' else 1

            # ______ (｡◔‿◔｡) ________ End of code

            else:
                available_payment_method_lines = pay.available_payment_method_line_ids

                # Select the first available one by default.
                if pay.payment_method_line_id in available_payment_method_lines:
                    pay.payment_method_line_id = pay.payment_method_line_id
                elif available_payment_method_lines:
                    pay.payment_method_line_id = available_payment_method_lines[0]._origin
                else:
                    pay.payment_method_line_id = False

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):
            if pay.move_id.statement_line_id:
                continue
            print('pay', pay.taxes_id.ids)
            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                for line in all_lines:
                    if line.parent_state != 'posted':
                        line.tax_ids = [(6, 0, pay.taxes_id.ids)]
                print('all_lines', all_lines)

                #  /\_/\
                # ( ◕‿◕ )
                #  >   <
                # Beginning: Ehab
                if self.env.context.get('sanad'):
                    writeoff_lines = None
                    if len(all_lines) > 2:
                        liquidity_lines, counterpart_lines = all_lines[0:2]
                    else:
                        liquidity_lines, counterpart_lines = all_lines
                else:
                    liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                # (｡◔‿◔｡) End of code

                if len(liquidity_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one outstanding payments/receipts account.",
                        move.display_name,
                    ))

                if len(counterpart_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one receivable/payable account (with an exception of "
                        "internal transfers).",
                        move.display_name,
                    ))

                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, "
                        "all optional journal items must share the same account.",
                        move.display_name,
                    ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same partner.",
                        move.display_name,
                    ))

                if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,

                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _seek_for_lines(self):
        if not self.is_sanad:  # Keep the original code
            ''' Helper used to dispatch the journal items between:
            - The lines using the temporary liquidity account.
            - The lines using the counterpart account.
            - The lines being the write-off lines.
            :return: (liquidity_lines, counterpart_lines, writeoff_lines)
            '''
            self.ensure_one()

            liquidity_lines = self.env['account.move.line']
            counterpart_lines = self.env['account.move.line']
            writeoff_lines = self.env['account.move.line']

            for line in self.move_id.line_ids:
                if line.account_id in self._get_valid_liquidity_accounts():
                    liquidity_lines += line
                elif line.account_id.internal_type in (
                        'receivable', 'payable') or line.partner_id == line.company_id.partner_id:
                    counterpart_lines += line
                else:
                    writeoff_lines += line

            return liquidity_lines, counterpart_lines, writeoff_lines
        else:
            liquidity_lines = self.env['account.move.line']
            counterpart_lines = self.env['account.move.line']
            writeoff_lines = self.env['account.move.line']
            liquidity_lines, counterpart_lines = self.line_ids[0:2]
            return liquidity_lines, counterpart_lines, writeoff_lines

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('sanad'):
            vals_list[0]['is_sanad'] = True
            if self.env.context.get('default_sanad_type')=='bank':
                vals_list[0]['sanad_type'] = 'bank'
            elif  self.env.context.get('default_payment_type')=='outbound':
                vals_list[0]['sanad_type'] = 'out'
            elif  self.env.context.get('default_payment_type')=='inbound':
                vals_list[0]['sanad_type'] = 'in'

            vals_list[0]['payment_method_line_id'] = 2 if self.env.context.get(
                'default_payment_type') == 'outbound' else 1
            # Update Context
            new_context = dict(self.env.context)
            new_context['journal_id'] = vals_list[0]['journal_id']
            new_context['destination_journal_id'] = vals_list[0]['destination_journal_id']
            new_context['taxes_id'] = vals_list[0]['taxes_id']
            self = self.with_context(new_context)
        payments = super().create(vals_list)
        return payments


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_sanad = fields.Boolean(related='payment_id.is_sanad')

    def update_vals(self, vals, sanad_type):
        if sanad_type == 'send_receive':
            cash_account_id = self.env['account.account'].search([('code', '=', '1201001')])
            sanad_account_id = self.journal_id.sanad_account_id or self.journal_id.default_account_id

            for line in vals.get('line_ids'):
                if self.env.context.get('default_payment_type') == 'outbound':
                    if line[2]['credit'] > 0:
                        line[2]['account_id'] = cash_account_id.id
                    else:
                        line[2]['account_id'] = sanad_account_id.id
                else:
                    if line[2]['debit'] > 0:
                        line[2]['account_id'] = cash_account_id.id
                    else:
                        line[2]['account_id'] = sanad_account_id.id

        elif sanad_type == 'internal_transfer':
            destination_journal = self.env['account.journal'].browse(self.env.context.get('destination_journal_id'))
            source_account_id = self.journal_id.sanad_account_id or self.journal_id.default_account_id
            destination_account_id = destination_journal.sanad_account_id or destination_journal.default_account_id

            if vals.get('line_ids'):

                sum_taxes = 0.0

                # Get the taxes_ids value from the context
                taxes_ids = self.env.context.get('taxes_id')

                if taxes_ids:
                    taxes_records = self.env['account.tax'].browse(taxes_ids[0][2])

                    for tax_record in taxes_records:
                        sum_taxes += tax_record.amount
                    new_vals = []

                for line in vals.get('line_ids'):
                    if line[2]['credit'] > 0:
                        line[2]['account_id'] = source_account_id.id
                        new_vals.append(line)

                    else:
                        amount = line[2]['debit']
                        line[2]['account_id'] = destination_account_id.id
                        line[2]['debit'] = line[2]['debit'] - (sum_taxes / 100) * line[2]['debit']

                        # Duplicate the line with modified fields
                        new_line = (0, 0, line[2].copy())
                        new_line[2]['debit'] = amount - line[2]['debit']
                        new_line[2]['account_id'] = 42
                        new_line[2]['name'] = 'الضريبة'

                        # Add the modified original line and the new line to the new_vals list
                        new_vals.append(line)
                        new_vals.append(new_line)

                # Replace the old vals['line_ids'] with the new list
                vals['line_ids'] = new_vals

        return vals

    def write(self, vals):
        if not self.env.context.get('default_is_internal_transfer') and self.env.context.get('sanad'):
            #  /\_/\
            # ( ◕‿◕ )
            #  > ^ <
            # The two parties of the move will be : 1- Cash and 2- Whatever account bound to the journal
            # In order for the other account of the move to appear in the Partner Ledger, it must fulfill these conditions:
            #  1- Internal Type: "receivable" or "payable"
            #  2- Not a liquidity account
            #  3- Bound to the journal (sanad_account_id)
            if vals.get('line_ids'):
                vals = self.update_vals(vals, 'send_receive')
        elif self.env.context.get('default_is_internal_transfer') and self.env.context.get('sanad'):
            vals = self.update_vals(vals, 'internal_transfer')

        res = super(AccountMove, self).write(vals)
        return res
