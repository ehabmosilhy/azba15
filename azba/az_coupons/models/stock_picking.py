# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"
    coupon_purchase_id = fields.Many2one('coupon.purchase', string="coupon Purchase")



class StockMove(models.Model):
    _inherit = "stock.move"
    coupon_purchase_id = fields.Many2one('coupon.purchase', string="coupon Purchase")
