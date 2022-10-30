# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAccountCategory(models.Model):
    _name = 'account.account.category'
    _order = "code"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    debit = fields.Float(compute="_compute_debit_credit_value", store=False,)
    credit = fields.Float(compute="_compute_debit_credit_value", store=False,)
    total = fields.Float(compute="_compute_balance_value", store=False, string="المستوى الرئيسي",)
    type = fields.Selection([
        ('account', 'Account'),
        ('level', 'Level')
    ], default="account", require=True)
    account_ids = fields.Many2many('account.account')
    account_level_ids = fields.One2many('account.account.category', 'parent_id',)
    parent_id = fields.Many2one('account.account.category', string="Root")

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique!')
    ]

    @api.depends('debit', 'credit')
    def _compute_balance_value(self):
        for record in self:
            record.total = record.debit - record.credit

    def _compute_debit_credit_value(self):
        for account in self:
            d = 0.00
            c = 0.00
            if account.type == "account":
                for a in account.account_ids:
                    d += (a.debit or 0.00)
                    c += (a.credit or 0.00)
                account.debit = d
                account.credit = c
            else:
                ll_ids = self.search([('id', 'child_of', account.id), ('type', '=', 'account')])
                for l in ll_ids:
                    for ll in l.account_ids:
                        d += (ll.debit or 0.00)
                        c += (ll.credit or 0.00)
                account.debit = d
                account.credit = c

    def _compute_debit_credit_value_account(self):
        categories = [category for category in self]
        for index, category in enumerate(categories):
            all_accounts = self.env['account.account'].search([('id', 'in', category.account_ids.ids)])
            self._compute_debit_creddit(all_accounts, categories, index)

    def _compute_debit_credit_value_level(self):
        levels = [level for level in self]
        for index, level in enumerate(levels):
            all_categories = self.env['account.account.category'].search([('id', 'in', level.account_level_ids.ids)])
            self._compute_debit_creddit(all_categories, levels, index)

    @staticmethod
    def _compute_debit_creddit(searche_res, self_contain, index):
        if len(list(searche_res)) > 0:
            debit, credit = 0, 0
            for acc in searche_res:
                debit += acc.debit
                credit += acc.credit
            self_contain[index].debit = debit
            self_contain[index].credit = credit
