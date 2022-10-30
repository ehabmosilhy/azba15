# -*- coding: utf-8 -*-


from odoo import api, models, _


class BankLetterPayroll(models.AbstractModel):
    _name = 'report.ejad_erp_hr.report_bank_letter_payroll'
    _description = 'Report Bank Letter Payroll'

    @api.model
    def _get_report_values(self, docids, data=None):
        line_ids = self.env['hr.payroll.advice.line'].search([('id', 'in', data['form'][0]['line_ids'])])
        docargs = {
            'data': data['form'][0],
            'line_ids': line_ids,
            'company_id': self.env.user.company_id,

        }
        return docargs
