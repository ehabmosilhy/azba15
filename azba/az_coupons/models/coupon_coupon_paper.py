# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class CouponPaper(models.Model):
    _name = 'az.coupon.paper'
    _description = "Coupon Paper"
    _rec_name = 'code'

    coupon_book_id = fields.Many2one('az.coupon', string='Coupon Book', ondelete='cascade')
    code = fields.Char(required=True, readonly=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('sent', 'Sent'),
        ('used', 'Used'),
        ('cancel', 'Cancelled')
    ], required=True, default='valid')
    date_used = fields.Datetime(string='Date Used')