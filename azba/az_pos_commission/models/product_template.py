# -*- coding: utf-8 -*-

from odoo import fields, models


class PosCommissionProduct(models.Model):
    _inherit = 'product.template'
    _description = 'Commission Products'
    commission_category = fields.Many2one('az.commission.category', string='فئة العمولة')
