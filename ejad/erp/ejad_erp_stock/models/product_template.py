# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _name = 'product.template'
    _description = 'Product Template'
    _inherit = ['product.template']
    _order = 'name'

    route_selection = fields.Selection([
        ('buy', 'Buy Direct'),
        ('check', 'check before receipt')], "طريقة الإستلام", default='check')

    @api.onchange('route_selection')
    def _on_change_route_selection(self):
        if self.route_selection == 'buy':
            self.route_ids = [(6, False, [self.env.ref('ejad_erp_stock.route_warehouse0_buy').id])]

        else:
            self.route_ids = [(6, False, [self.env.ref('ejad_erp_stock.route_warehouse0_check_before_receipt').id])]

