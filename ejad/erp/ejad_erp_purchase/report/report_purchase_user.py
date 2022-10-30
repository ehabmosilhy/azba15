# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPurchaseUser(models.AbstractModel):
    _name = 'report.ejad_erp_purchase.report_purchase_user'

    @api.model
    def _get_report_values(self, docids, data=None):

        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, info):
        domain =[('purchase_representative', '=', info['user_id'][0])]
        if info['date_from']:
            domain += [('date', '>=', info['date_from'])]
        if info['date_to']:
            domain += [('date', '<=', info['date_to'])]
        orders = self.env['purchase.requisition.request'].search(domain)

        return orders
