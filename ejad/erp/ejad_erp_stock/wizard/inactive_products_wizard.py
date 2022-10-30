# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class InActiveProductReport(models.TransientModel):
    _name = 'wiz.inactive.product.report'
    _description = 'Retrieve Product with no moves for specific time'

    location_id = fields.Many2one('stock.location')
    date_from = fields.Datetime(string='تاريخ البدء')
    date_to = fields.Datetime(string='تاريخ الانتهاء')

    def check_report(self):
        data = {}
        data['form'] = self.read(['location_id', 'date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('ejad_erp_stock.action_inactive_product_report').report_action(self, data=data)
