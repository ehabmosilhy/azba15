# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_to_number = fields.Char(string="WhatsApp To Number")
    whatsapp_from_number = fields.Char(string="WhatsApp From Number")
    twilio_account_sid = fields.Char(string="Twilio Account SID")
    twilio_auth_token = fields.Char(string="Twilio Auth Token")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        res.update(
            whatsapp_to_number=IrConfigParam.get_param('az_coupons.whatsapp_to_number'),
            whatsapp_from_number=IrConfigParam.get_param('az_coupons.whatsapp_from_number'),
            twilio_account_sid=IrConfigParam.get_param('az_coupons.twilio_account_sid'),
            twilio_auth_token=IrConfigParam.get_param('az_coupons.twilio_auth_token'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        IrConfigParam.set_param('az_coupons.whatsapp_to_number', self.whatsapp_to_number)
        IrConfigParam.set_param('az_coupons.whatsapp_from_number', self.whatsapp_from_number)
        IrConfigParam.set_param('az_coupons.twilio_account_sid', self.twilio_account_sid)
        IrConfigParam.set_param('az_coupons.twilio_auth_token', self.twilio_auth_token)
