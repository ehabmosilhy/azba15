# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

'''
Remove the Opening Balance Difference from POS
'''


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def write(self, values):
        values['balance_start'] = 0
        res = super(AccountBankStatement, self).write(values)
        for line in self.line_ids:
            if "difference" in line.payment_ref.lower() or line.amount < 0:
                line.unlink()
        return res
