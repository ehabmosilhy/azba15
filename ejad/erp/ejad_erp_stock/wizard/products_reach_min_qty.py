# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductReachMInQyt(models.TransientModel):
    _name = 'wiz.product.min.qyt.report'
    _description = 'Retrieve Products that reach min qyt'

    date_from = fields.Datetime(string='تاريخ البدء')
    date_to = fields.Datetime(string='تاريخ الانتهاء')

    def check_report(self):
        data = {}
        data['form'] = self.read(['date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('ejad_erp_stock.action_product_min_qty').report_action(self, data=data)
