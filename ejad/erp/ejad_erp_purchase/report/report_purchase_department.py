# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPurchaseDepartment(models.AbstractModel):
    _name = 'report.ejad_erp_purchase.report_purchase_department'

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
        orders = self.env['purchase.requisition.request'].search([('department_id', '=', info['department_id'][0]),
                                                    ('date', '>=', info['date_from']),
                                                    ('date', '<=', info['date_to'])
                                                    ])

        return orders
