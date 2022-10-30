# -*- coding: utf-8 -*-


from odoo import api, models, _


class BankLetter(models.AbstractModel):
    _name = 'report.ejad_erp_hr.report_bank_letter'
    _description = 'Report Bank Letter'

    @api.model
    def _get_report_values(self, docids, data=None):

        docargs = {
            'data': data['form'][0],
            'company_id': self.env.user.company_id,

        }
        return docargs
