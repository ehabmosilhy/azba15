from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    qty_in_src_location = fields.Float(compute='_compute_qty_in_src_location', string='Quantity in Source Location')

    @api.depends('picking_id.location_id', 'product_id')
    def _compute_qty_in_src_location(self):
        for move in self:
            location_id = move.picking_id.location_id
            product_id = move.product_id
            if location_id and product_id:
                quants = self.env['stock.quant'].search([
                    ('location_id', '=', location_id.id),
                    ('product_id', '=', product_id.id)
                ])
                move.qty_in_src_location = sum(quant.quantity for quant in quants)
            else:
                move.qty_in_src_location = 0.0

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('location_id')
    def _onchange_location_id(self):
        for move in self.move_ids_without_package:
            move._compute_qty_in_src_location()
