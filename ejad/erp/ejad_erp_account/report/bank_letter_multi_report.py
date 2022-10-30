# -*- coding: utf-8 -*-


from odoo import api, models, _


class BankLetterMulti(models.AbstractModel):
    _name = 'report.ejad_ejad_erp_account.report_bank_letter_multi'

    @api.model
    def get_report_values(self, docids, data=None):
        line_ids = self.env['account.invoice.multi.partners.line'].search([('id', 'in', data['form'][0]['line_ids'])])
        docargs = {
            'data': data['form'][0],
            'line_ids': line_ids,
            'company_id': self.env.user.company_id,

        }
        return docargs
