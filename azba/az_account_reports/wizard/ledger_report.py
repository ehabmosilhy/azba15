# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import  ValidationError

class LedgerReport(models.TransientModel):
    _name = "az.ledger.report"
    _description = "Ledger Report"

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    company_id = fields.Many2one('res.company',string="Company", default=lambda self: self.env.company
                                 , required=True)
    account_ids = fields.Many2one("account.account", string="Accounts")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("End date must be greater than start date!")

    def get_ledger_report(self):
        [data] = self.read()
        datas = {
             'ids': [1],
             'model': 'az.ledger.report',
             'form': data
        }
        action = self.env.ref('az_account_reports.ledger_report_action_view').report_action(self, data=datas)
        return action
