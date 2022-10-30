# -*- coding: utf-8 -*-

from odoo import api, models, _


class ReportACOperationMove(models.AbstractModel):
    _name = 'report.ejad_erp_administrative_communications.report_op_move'
    _description = 'Report op move'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'operation': self.env['ac.operation'].search([('id', '=', data['form']['operation_id'][0])]),
            'lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, info):
        move_ids = self.env['ac.operation.move'].search([('operation_id', '=', info['operation_id'][0]),
                                                         ('type', '=', 'transfer')])
        return move_ids
