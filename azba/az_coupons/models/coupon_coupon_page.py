# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class CouponPage(models.Model):
    _name = 'az.coupon.page'
    _description = "Coupon Page"
    _rec_name = 'code'

    partner_id = fields.Many2one('res.partner')
    coupon_book_id = fields.Many2one('az.coupon', string='Coupon Book', ondelete='cascade')
    code = fields.Char(required=True, readonly=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('used', 'Used'),
    ], required=True, default='valid')
    date_used = fields.Datetime(string='Date Used')
    pos_session_id = fields.Many2one('pos.session', string='Session', ondelete='cascade', readonly=True)
    active = fields.Boolean(string='Active', default=True)

    order_id = fields.Many2one('pos.order', string='Order', ondelete='cascade')
    def write(self, vals):
        if "state" in vals:
            if vals["state"] == "used":
                vals["date_used"] = fields.Datetime.now()
            else:
                vals["date_used"] = None
            
        result = super(CouponPage, self).write(vals)
    
