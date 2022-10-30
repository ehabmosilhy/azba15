# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class ACOperationReport(models.TransientModel):
    _name = 'wiz.operation.report'
    _description = 'wiz operation report'

    report_type = fields.Selection([
        ('in', 'وارد العام'),
        ('out', 'صادر العام'),
        ('internal', 'معاملة الداخلية')], string="نوع المعاملة", required=True)

    operation_id = fields.Many2one(comodel_name="ac.operation", string="المعاملة")

    
    @api.onchange('report_type')
    def onchange_report_type(self):
        for rec in self:
            if rec.report_type == 'in':
                return {'domain': {'operation_id': [('type', '=', 'in')]}}
            elif rec.report_type == 'out':
                return {'domain': {'operation_id': ['|', ('type', '=', 'out'), ('is_global_outbox', '=', True)]}}
            elif rec.report_type == 'internal':
                return {'domain': {'operation_id': [('type', '=', 'internal')]}}
            else:
                return {'domain': {'operation_id': []}}
    
    def check_report(self):

        data = dict()
        data['form'] = self.read(['operation_id'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('ejad_erp_administrative_communications.action_operation_report').report_action(self, data=data)

    
    def check_report_move(self):
        data = dict()
        data['form'] = self.read(['operation_id'])[0]
        return self._print_report_move(data)

    def _print_report_move(self, data):
        return self.env.ref('ejad_erp_administrative_communications.action_operation_report_move').report_action(self, data=data)
