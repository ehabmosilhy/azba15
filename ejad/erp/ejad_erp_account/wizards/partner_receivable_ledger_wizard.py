# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PartnerReceivableReport(models.TransientModel):
    _name = "partner.receivable.ledger.wizard"
    _description = "Partner Receivable Report"

    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    contact_type = fields.Selection(
        selection=[('company', 'Client'), ('student', 'Student'), ('both', 'Client or Student')], string='Customer Type')
    report_type = fields.Selection(
        selection=[('detailed', 'Detailed'), ('summery', 'Summery')], default='detailed', string='Report Display')
    partner_ids = fields.Many2many('res.partner', string='Client/Student')

    @api.onchange('contact_type')
    def _onchange_contract_type(self):
        if self.contact_type == 'company':
            domain = [('child_ids', '!=', False), ('parent_id', '=', False)]
        elif self.contact_type == 'student':
            domain = [('child_ids', '=', False), ('parent_id', '=', False)]
        else:
            domain = [('parent_id', '=', False)]
        return {'domain': {'partner_ids': domain}}

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        return result

    def _print_report(self, data):
        # data = self.pre_print_report(data)
        return self.env.ref('ejad_erp_account.action_partner_receivable_ledger').report_action(self, data=data)

    def check_report(self):
        # self.ensure_one()
        data = {}
        # data['ids'] = self.env.context.get('active_ids', [])
        # data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'report_type', 'contact_type', 'partner_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)
