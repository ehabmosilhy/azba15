# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime


class ReportProductMINQty(models.AbstractModel):
    _name = 'report.ejad_erp_stock.report_product_min_qty'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, info):
        order_purchase_line = self.env['purchase.order.line'].search([('orderpoint_id', '!=', False),
                                                                      ('date_order', '>=', info['date_from']),
                                                                      ('date_order', '<=', info['date_to'])
                                                                      ])

        return order_purchase_line
