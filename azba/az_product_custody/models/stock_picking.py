# -*- coding: utf-8 -*-
from odoo import fields, models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custody_product_exists = fields.Boolean(
        string="صنف عهدة",
        compute='_compute_custody_product_exists'
    )

    @api.onchange('move_ids_without_package')
    def _compute_custody_product_exists(self):
        for record in self:
            custody_products = self.env['product.custody'].search([])
            custody_product_ids = custody_products.mapped('product_id').ids
            record.custody_product_exists = any(
                move.product_id.id in custody_product_ids for move in record.move_ids_without_package
            )

