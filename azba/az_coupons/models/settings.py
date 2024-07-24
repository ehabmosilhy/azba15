# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CouponBookProduct(models.Model):
    _name = 'coupon.book.product'
    _description = 'Coupon Book Product'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    page_count = fields.Integer(string="Page Count", required=True)

class CouponBookProductLine(models.TransientModel):
    _name = 'coupon.book.product.line'
    _description = 'Coupon Book Product Line'

    config_id = fields.Many2one('res.config.settings', string="Config")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    page_count = fields.Integer(string="Page Count", required=True, default=1)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    coupon_page_product = fields.Many2one('product.product', string="Coupon Page Product")
    coupon_book_product_ids = fields.One2many('coupon.book.product.line', 'config_id', string="Coupon Book Products")

    whatsapp_to_number = fields.Char(string="WhatsApp To Number")
    whatsapp_from_number = fields.Char(string="WhatsApp From Number")
    twilio_account_sid = fields.Char(string="Twilio Account SID")
    twilio_auth_token = fields.Char(string="Twilio Auth Token")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()

        # Get the existing coupon book products
        coupon_book_products = self.env['coupon.book.product'].search([])

        # Get the coupon page product
        coupon_page_product_id = IrConfigParam.get_param('az_coupons.coupon_page_product')
        coupon_page_product = False
        if coupon_page_product_id:
            coupon_page_product = int(coupon_page_product_id)

        res.update(
            whatsapp_to_number=IrConfigParam.get_param('az_coupons.whatsapp_to_number'),
            whatsapp_from_number=IrConfigParam.get_param('az_coupons.whatsapp_from_number'),
            twilio_account_sid=IrConfigParam.get_param('az_coupons.twilio_account_sid'),
            twilio_auth_token=IrConfigParam.get_param('az_coupons.twilio_auth_token'),
            coupon_page_product=coupon_page_product,
            coupon_book_product_ids=[(0, 0, {'product_id': p.product_id.id, 'page_count': p.page_count}) for p in
                                     coupon_book_products],
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        IrConfigParam.set_param('az_coupons.whatsapp_to_number', self.whatsapp_to_number)
        IrConfigParam.set_param('az_coupons.whatsapp_from_number', self.whatsapp_from_number)
        IrConfigParam.set_param('az_coupons.twilio_account_sid', self.twilio_account_sid)
        IrConfigParam.set_param('az_coupons.twilio_auth_token', self.twilio_auth_token)
        IrConfigParam.set_param('az_coupons.coupon_page_product', self.coupon_page_product.id if self.coupon_page_product else False)

        # Update coupon book products
        existing_products = self.env['coupon.book.product'].search([])
        existing_products.unlink()
        for line in self.coupon_book_product_ids:
            self.env['coupon.book.product'].create({
                'product_id': line.product_id.id,
                'page_count': line.page_count,
            })