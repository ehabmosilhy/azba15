# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

from datetime import datetime

class CouponPaper(models.Model):
    _name = 'coupon.coupon.paper'

    _description = "Coupon Paper"
    _rec_name = 'code'

    coupon_book_id = fields.Many2one('coupon.coupon', string='Coupon Book', ondelete='cascade')

    code = fields.Char(required=True, readonly=True)
    state = fields.Selection([
        ('new', 'Valid'),
        ('sent', 'Sent'),
        ('used', 'Used'),
        ('cancel', 'Cancelled')
    ], required=True, default='new')
