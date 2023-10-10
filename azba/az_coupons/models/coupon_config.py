# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    coupon_product_id = fields.Many2one('product.product', string="Product", required=True)
    coupon_book_ids = fields.One2many("coupon.book", "product_id")

# class CouponConfig(models.Model):
#     _name = "coupon.config"
#     coupon_product_id = fields.Many2one('product.product', string="Product", required=True)
#     coupon_book_ids = fields.One2many("coupon.book","product_id")

class CouponBook(models.Model):
    _name = "coupon.book"
    product_id = fields.Many2one('product.product', string='Product')
    page_count = fields.Integer(string='Page Count')