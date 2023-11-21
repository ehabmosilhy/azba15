# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    coupon_product_id = fields.Many2one('product.product', string='Voucher Product', help='Product used for paper (voucher)')
    coupon_book_ids = fields.Many2many("coupon.book", help='Number of vouchers in each book')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        coupon_product_id = ICPSudo.get_param('az_coupons.coupon_product_id')
        coupon_book_ids = ICPSudo.get_param('az_coupons.coupon_book_ids')
        res.update(
            coupon_product_id=int(coupon_product_id) if coupon_product_id else False,
            coupon_book_ids=[(6, 0, [int(_) for _ in coupon_book_ids.split(',')] )] if coupon_book_ids else False
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("az_coupons.coupon_product_id", self.coupon_product_id.id)
        ICPSudo.set_param("az_coupons.coupon_book_ids", ','.join(map(str, self.coupon_book_ids.ids)))


class CouponBook(models.Model):
    _name = "coupon.book"
    product_id = fields.Many2one('product.product', string='Voucher Product', help='Product used for paper (voucher)')
    paper_count = fields.Integer(string='Paper Count', help='Number of vouchers in each book')


