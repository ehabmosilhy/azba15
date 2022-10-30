# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime


class ReportInactiveProduct(models.AbstractModel):
    _name = 'report.ejad_erp_stock.report_inactive_product'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'products': self.get_lines(data.get('form')),
            'last_move_dates': self.get_move_last_dates(data.get('form')),
        }

    @api.model
    def get_lines(self, info):
        all_products = self.env['product.product'].search([('type', '!=', 'service')]).ids
        product_moves = self.env['stock.move.line'].search([('location_id', '=', info['location_id'][0]),
                                                            ('date', '>=', info['date_from']),
                                                            ('date', '<=', info['date_to'])
                                                            ])

        product_has_moves = set([line.product_id.id for line in product_moves])

        inactive_product = [x for x in all_products if x not in product_has_moves]

        inactive_products_line = self.env['product.product'].search([('id', 'in', inactive_product)])
        return inactive_products_line

    def get_move_last_dates(self, info):
        dic = {}
        inactive_products = self.get_lines(info)
        for product in inactive_products:
            product_moves = self.env['stock.move.line'].search([('product_id', '=', product.id),
                                                                ('location_id', '=', info['location_id'][0])])
            if product_moves:
                last_date = datetime.strptime(product_moves[-1].date, DATETIME_FORMAT).strftime("%y/%m/%d %S:%M:%H")
                dic.update({product.id: last_date})
            else:
                dic.update({product.id: ''})

        return dic
