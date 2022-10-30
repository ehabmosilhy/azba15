# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseReport(models.TransientModel):
    _name = 'wiz.purchase.report'
    _description = 'Purchase Order by category'

    department_id = fields.Many2one('hr.department', string="الادارة",)
    date_from = fields.Datetime(string='تاريخ البدء')
    date_to = fields.Datetime(string='تاريخ الانتهاء')

    def check_report(self):
        data = {}
        data['form'] = self.read(['department_id', 'date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('ejad_erp_purchase.action_purchase_department_report').report_action(self, data=data)
