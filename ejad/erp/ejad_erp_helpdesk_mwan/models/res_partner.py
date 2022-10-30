# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tax_reg_no = fields.Char(string="Tax registration No")
    commercial_reg_no = fields.Char(string="Commercial registration No")