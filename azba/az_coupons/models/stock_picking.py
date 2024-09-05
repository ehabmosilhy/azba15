# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        """Don't create picking for coupon books"""
        if any(line.product_id.id in (37, 38) for line in lines):
            lines = []
        return super(StockPicking, self)._create_picking_from_pos_order_lines(location_dest_id, lines, picking_type,
                                                                              partner)
