# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseReport(models.TransientModel):
    _name = 'wiz.material.price'
    _description = 'Material Price'

    category_id = fields.Many2one('product.category', string="الفئة", )

    def check_report(self):
        data = {}
        data['form'] = self.read(['category_id'])[0]

        return self._print_report(data)

    def _print_report(self, data):

        return self.env.ref('ejad_erp_purchase.action_material_price_report').report_action(self, data=data)
