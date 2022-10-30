# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAccountDebitCredit(models.Model):
    _inherit = 'account.account'

    debit = fields.Float(readonly=True, compute="_compute_debit_credit_value", stor=True)
    credit = fields.Float(readonly=True, compute="_compute_debit_credit_value", stor=True)
    total = fields.Float(readonly=True, compute="_compute_balance_value", stor=True, string="Balance")

    @api.depends('debit', 'credit')
    def _compute_balance_value(self):
        for record in self:
            record.total = record.debit - record.credit

    def _compute_debit_credit_value(self):
        for record in self:
            all_accounts = self.env['account.move.line'].search([('account_id', '=', record.id)])
            if len(list(all_accounts)) > 0:
                debit = 0
                credit = 0
                for account in all_accounts:
                    debit += account.debit
                    credit += account.credit
                record.debit = debit
                record.credit = credit
            else:
                record.debit = 0
                record.credit = 0
