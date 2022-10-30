# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseReport(models.TransientModel):
    _name = 'wiz.po.user'
    _description = 'Purchase Order by category'

    user_id = fields.Many2one('res.users', string="المستخدم",domain=lambda self:[('groups_id', '=', self.env.ref('ejad_erp_purchase.group_purchase_user').id)])
    date_from = fields.Datetime(string='تاريخ البدء')
    date_to = fields.Datetime(string='تاريخ الانتهاء')

    def check_report(self):
        data = {}
        data['form'] = self.read(['user_id', 'date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('ejad_erp_purchase.action_purchase_user_report').report_action(self, data=data)
