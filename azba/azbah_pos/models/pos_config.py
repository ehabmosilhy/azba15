# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'
    _description = 'Point of Sale Configuration'

    allowed_users = fields.Many2many("res.users")

    # Show only some partners
    def get_limited_partners_loading(self):
        partners = self.env['res.partner'].search([('pos_config_ids', 'in', self.id)]).mapped("id")
        result = [(_,) for _ in partners]
        return result
