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

    @api.depends('partner_id', 'destination_account_id', 'journal_id')
    def _compute_is_internal_transfer(self):
        if not self.env.context.get('sanad'):
            for payment in self:
                payment.is_internal_transfer = payment.partner_id and payment.partner_id == payment.journal_id.company_id.partner_id

    @api.onchange('posted_before', 'state', 'journal_id', 'date')
    def _onchange_journal_date(self):
        # Before the record is created, the move_id doesn't exist yet, and the name will not be
        # recomputed correctly if we change the journal or the date, leading to inconsitencies
        if not self.env.context.get('sanad'):
            if not self.move_id:
                self.name = False

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if not self.env.context.get('sanad'):
            self.move_id._onchange_journal()

    @api.depends('is_internal_transfer')
    def _compute_partner_id(self):
        if not self.env.context.get('sanad'):
            for pay in self:
                if pay.is_internal_transfer:
                    pay.partner_id = pay.journal_id.company_id.partner_id
                elif pay.partner_id == pay.journal_id.company_id.partner_id:
                    pay.partner_id = False
                else:
                    pay.partner_id = pay.partner_id

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('sanad'):
            vals_list[0]['is_internal_transfer'] = True
            vals_list[0]['payment_method_line_id'] = 4
            vals_list[0]['destination_journal_id'] = 9
        payments = super().create(vals_list)

        return payments

    def _seek_for_lines(self):
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

        if self.env.context.get('sanad'):
            for line in self.move_id.line_ids:
                if line.account_id in self._get_valid_liquidity_accounts():
                    liquidity_lines += line
                elif line.account_id.internal_type in (
                        'receivable',
                        'payable') or line.partner_id == line.company_id.partner_id or self.env.context.get('sanad'):
                    counterpart_lines += line
                else:
                    writeoff_lines += line
        else:
            for line in self.move_id.line_ids:
                if line.account_id in self._get_valid_liquidity_accounts():
                    liquidity_lines += line
                elif line.account_id.internal_type in (
                        'receivable', 'payable') or line.partner_id == line.company_id.partner_id:
                    counterpart_lines += line
                else:
                    writeoff_lines += line

        return liquidity_lines, counterpart_lines, writeoff_lines


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        if self.env.context.get('sanad'):
            # get cash account id
            cash_account_id = self.env['account.account'].search([('code', '=', '1201001')])
            if vals.get('line_ids'):
                for line in vals.get('line_ids'):
                    if self.env.context.get('default_payment_type') == 'outbound':
                        if line[2]['credit'] > 0:
                            line[2]['account_id'] = cash_account_id.id
                        else:
                            line[2]['account_id'] = self.journal_id.default_account_id.id
                    else:
                        if line[2]['debit'] > 0:
                            line[2]['account_id'] = cash_account_id.id
                        else:
                            line[2]['account_id'] = self.journal_id.default_account_id.id

        res = super(AccountMove, self).write(vals)
        return res
