# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_payment_display_name(self):
        '''
        Hook method for inherit
        When you want to set a new name for payment, you can extend this method
        '''
        if not self.env.context.get('sanad'):
            return {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }
        else:
            return {
                'outbound-customer': "",
                'inbound-customer': "",
                'outbound-supplier': "",
                'inbound-supplier': "",
            }

    # -------------------------------------------------------------------------
    # SYNCHRONIZATION account.payment <-> account.move
    # -------------------------------------------------------------------------

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids

                # -------------------------------------------------------------------------
                # Azbah
                # -------------------------------------------------------------------------

                if self.env.context.get('sanad'):
                    writeoff_lines = None
                    liquidity_lines, counterpart_lines = all_lines
                else:
                    liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()



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

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('sanad'):
            # vals_list[0]['is_internal_transfer'] = True
            vals_list[0]['payment_method_line_id'] = 4
            # vals_list[0]['destination_journal_id'] = 9
        payments = super().create(vals_list)

        return payments


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        if self.env.context.get('sanad'):
            # get cash account id
            cash_account_id = self.env['account.account'].search([('code', '=', '1201001')])
            receivable_id = self.env['account.account'].search([('code', '=', '102011')])
            payables_id = self.env['account.account'].search([('code', '=', '201002')])

            # 102011 Accounts Receivable
            # 201002 Payables

            if vals.get('line_ids'):
                for line in vals.get('line_ids'):
                    # if self.env.context.get('default_payment_type') == 'outbound':
                    if line[2]['account_id'] == receivable_id.id:
                        line[2]['account_id'] = cash_account_id.id
                    else:
                        line[2]['account_id'] = self.journal_id.inbound_payment_method_line_ids[0].payment_account_id.id


        res = super(AccountMove, self).write(vals)
        return res
