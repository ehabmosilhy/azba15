# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class TrainingFinancialReport(models.TransientModel):
    _name = "training.report.wizard"
    _description = "Partner Receivable Report"

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    contact_type = fields.Selection(
        selection=[('company', 'Client'), ('student', 'Student'), ('both', 'Client or Student')], string='Customer Type' ,default='both')
    partner_ids = fields.Many2many('res.partner', string='Client/Student')
    courses_ids = fields.Many2many('product.template', string='Training Courses', domain=lambda self: [
        ('categ_id', 'child_of', self.env.ref('ejad_erp_account.product_category_trqining').id)])

    @api.onchange('contact_type')
    def _onchange_contract_type(self):
        if self.contact_type == 'company':
            domain = [('child_ids', '!=', False), ('parent_id', '=', False)]
        elif self.contact_type == 'student':
            domain = [('child_ids', '=', False), ('parent_id', '=', False)]
        else:
            domain = [('parent_id', '=', False)]
        return {'domain': {'partner_ids': domain}}

    def _print_report(self, data):
        # data = self.pre_print_report(data)
        return self.env.ref('ejad_erp_account.action_training_course_report').report_action(self, data=data)

    def check_report(self):
        # self.ensure_one()
        data = {}
        # data['ids'] = self.env.context.get('active_ids', [])
        # data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to','courses_ids', 'contact_type', 'partner_ids'])[0]
        return self._print_report(data)
