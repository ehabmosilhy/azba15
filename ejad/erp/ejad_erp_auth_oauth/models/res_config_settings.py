# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auth_oauth_microsoft_enabled = fields.Boolean(string='Allow users to sign in with Microsoft')
    auth_oauth_microsoft_client_id = fields.Char(string='Microsoft Client ID')
    auth_oauth_microsoft_client_secret = fields.Char(string='Microsoft Client Secret')

    # Opt Fields
    signin_auth = fields.Boolean(string="تفعيل التسجيل عن طريق ال SMS")
    otp_time_limit = fields.Integer('صلاحية رمز التفعيل ', help="وقت صلاحية رمز التفعيل بالثواني")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        microsoft_provider = self.env.ref('ejad_erp_auth_oauth.provider_microsoft', False)
        res.update(
            auth_oauth_microsoft_enabled=microsoft_provider.enabled,
            auth_oauth_microsoft_client_id=microsoft_provider.client_id,
            auth_oauth_microsoft_client_secret=microsoft_provider.client_secret,
            signin_auth=IrDefault.get('res.config.settings', 'signin_auth') or False,
            otp_time_limit=IrDefault.get('res.config.settings', 'otp_time_limit') or 0,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        microsoft_provider = self.env.ref('ejad_erp_auth_oauth.provider_microsoft', False)
        microsoft_provider.write(
            {'enabled': self.auth_oauth_microsoft_enabled,
             'client_id': self.auth_oauth_microsoft_client_id,
             'client_secret': self.auth_oauth_microsoft_client_secret, })

        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings', 'signin_auth', self.signin_auth)
        IrDefault.set('res.config.settings', 'otp_time_limit',self.otp_time_limit)

