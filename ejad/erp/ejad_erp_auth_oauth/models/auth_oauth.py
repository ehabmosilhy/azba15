# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AuthOAuthProviderInherit(models.Model):
    _inherit = 'auth.oauth.provider'

    client_secret = fields.Char(string='Client Secret')
    response_type = fields.Selection([('token', 'Token'), ('code', 'Code')], default='token', required=True)
