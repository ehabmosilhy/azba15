# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportMaterialPrice(models.AbstractModel):
    _name = 'report.ejad_erp_purchase.report_material_price'

    @api.model
    def _get_report_values(self, docids, data=None):

        return {
            'data': data['form'],
            'lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, info):
        materials = self.env['product.template'].search([('qty_available', '>', 0),
                                                         ('categ_id', '=', info['category_id'][0])])

        return materials

