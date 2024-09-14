# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class CouponPage(models.Model):
    _name = 'az.coupon.page'
    _description = "Coupon Page"
    _rec_name = 'code'

    coupon_book_id = fields.Many2one('az.coupon', string='Coupon Book', ondelete='cascade')
    code = fields.Char(required=True, readonly=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('used', 'Used'),
    ], required=True, default='valid')
    date_used = fields.Datetime(string='Date Used')
    pos_session_id = fields.Many2one('pos.session', string='Session', ondelete='cascade', readonly=True)

    
    def write(self, vals):
        if "state" in vals and vals["state"] == "used":
            vals["date_used"] = fields.Datetime.now()
        result = super(CouponPage, self).write(vals)
