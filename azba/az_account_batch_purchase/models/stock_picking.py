# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"
    batch_purchase_id = fields.Many2one('batch.purchase', string="Batch Purchase")
    delegate_id = fields.Many2one(related='batch_purchase_id.delegate_id')



class StockMove(models.Model):
    _inherit = "stock.move"
    batch_purchase_id = fields.Many2one('batch.purchase', string="Batch Purchase")
    delegate_id = fields.Many2one(related='batch_purchase_id.delegate_id')
