# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportACOperation(models.AbstractModel):
    _name = 'report.ejad_erp_administrative_communications.report_operation'
    _description = 'Report Operation'

    @api.model
    def _get_report_values(self, docids, data=None):

        return {
            'operation': self.env['ac.operation'].search([('id', '=', data['form']['operation_id'][0])])
        }
