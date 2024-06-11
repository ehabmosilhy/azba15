# -*- coding: utf-8 -*-

from odoo import fields, models


class CustodyProduct(models.Model):
    _name = 'product.custody'
    _description = 'Custody Products'
    product_id = fields.Many2one('product.product', string="Product", required=True)
