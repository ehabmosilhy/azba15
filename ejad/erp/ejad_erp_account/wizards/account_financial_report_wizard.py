# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class NUASSReportFinancial(models.TransientModel):
    _inherit = "account.common.report"
    _name = "nauss.report.financial"
    _description = "NAUSS Financial Report"

    report_name = fields.Char(string='Report Name', required=True)
    account_ids = fields.Many2many('account.account', string='Accounts')
    account_type_ids = fields.Many2many('account.account.type', string='Account Type')
    initial_balance = fields.Boolean(string='Initial Balance')
    report_type = fields.Selection(
        selection=[('detailed', 'Detailed'), ('summery', 'Summery')], default='detailed', string='Report Display')

    journal_ids = fields.Many2many('account.journal', string='Journals', required=True)

    target_move = fields.Selection(default='all')

    @api.onchange('account_type_ids','company_id')
    def _onchange_account_type(self):
        domain =[]
        if self.account_type_ids:
            domain += [('user_type_id', 'in', self.account_type_ids.ids)]
        if self.company_id:
            domain += [('company_id', '=', self.company_id.id)]

        return {'domain': {'account_ids': domain}}

    def _print_report(self, data):
        data['form'].update(self.read(['initial_balance', 'account_type_ids', 'account_ids','report_name','report_type'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        return self.env.ref('ejad_erp_account.action_nauss_financial_report').with_context(
            landscape=True).report_action(self,data=data)
